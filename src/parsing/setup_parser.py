import ast
import re
from ..storage import Dependency, RelationType
from .requirements_parser import normalize_name


def parse_setup_py(content: str, source_pkg: str) -> list[Dependency]:
    """Parse setup.py using AST (never exec)."""
    if not content:
        return []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    deps = []
    visitor = SetupVisitor(source_pkg)
    visitor.visit(tree)

    deps.extend(visitor.dependencies)
    return deps


class SetupVisitor(ast.NodeVisitor):
    def __init__(self, source_pkg: str):
        self.source_pkg = source_pkg
        self.dependencies = []
        self.variables = {}

    def visit_Assign(self, node):
        # track variable assignments for later resolution
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            value = self._extract_value(node.value)
            if value is None and var_name == "deps":
                value = self._build_deps_lookup()
            if value is not None:
                self.variables[var_name] = value
        self.generic_visit(node)

    def visit_Call(self, node):
        func_name = self._get_func_name(node)
        if func_name in ('setup', 'setuptools.setup'):
            self._process_setup_call(node)
        self.generic_visit(node)

    def _get_func_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
        return ""

    def _process_setup_call(self, node):
        for keyword in node.keywords:
            if keyword.arg == 'install_requires':
                self._add_deps(keyword.value, RelationType.REQUIRES_CORE, 'setup.py')
            elif keyword.arg == 'setup_requires':
                self._add_deps(keyword.value, RelationType.REQUIRES_DEV, 'setup.py')
            elif keyword.arg == 'tests_require':
                self._add_deps(keyword.value, RelationType.REQUIRES_DEV, 'setup.py')
            elif keyword.arg == 'extras_require':
                self._process_extras(keyword.value)

    def _process_extras(self, node):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant):
                    extra_name = key.value
                    is_dev = extra_name in ('dev', 'test', 'testing', 'tests', 'develop')
                    rel_type = RelationType.REQUIRES_DEV if is_dev else RelationType.REQUIRES_OPTIONAL
                    self._add_deps(value, rel_type, f'setup.py[{extra_name}]')

    def _add_deps(self, node, rel_type: RelationType, source_file: str):
        deps_list = self._extract_value(node)
        if not isinstance(deps_list, list):
            return

        for dep_str in deps_list:
            if not isinstance(dep_str, str):
                continue
            dep = self._parse_dep_string(dep_str, rel_type, source_file)
            if dep:
                self.dependencies.append(dep)

    def _parse_dep_string(self, dep_str: str, rel_type: RelationType, source_file: str) -> Dependency | None:
        # strip environment markers
        dep_str = re.split(r'\s*;\s*', dep_str)[0].strip()

        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?\s*(.*)?$', dep_str)
        if not match:
            return None

        pkg_name = normalize_name(match.group(1))
        version = match.group(2).strip() if match.group(2) else None

        if not pkg_name or pkg_name == self.source_pkg:
            return None

        return Dependency(
            source=self.source_pkg,
            target=pkg_name,
            relation_type=rel_type,
            version_constraint=version,
            source_file=source_file
        )

    def _extract_value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._extract_value(el) for el in node.elts]
        elif isinstance(node, ast.Tuple):
            return tuple(self._extract_value(el) for el in node.elts)
        elif isinstance(node, ast.Dict):
            keys = [self._extract_value(k) for k in node.keys]
            values = [self._extract_value(v) for v in node.values]
            if any(k is None for k in keys) or any(v is None for v in values):
                return None
            return dict(zip(keys, values))
        elif isinstance(node, ast.DictComp):
            # handle patterns like: deps = {b: a for a, b in ... _deps ...}
            return self._build_deps_lookup()
        elif isinstance(node, ast.Subscript):
            container = self._extract_value(node.value)
            normalize_key = False

            if container is None and isinstance(node.value, ast.Name) and node.value.id == "deps":
                container = self.variables.get("deps") or self._build_deps_lookup()
                normalize_key = True
                if container is not None:
                    self.variables["deps"] = container

            if container is None:
                return None

            # slice can be Constant (py3.9+), Name, or another node
            idx = None
            if isinstance(node.slice, ast.Constant):
                idx = node.slice.value
            elif isinstance(node.slice, ast.Name):
                idx = self.variables.get(node.slice.id)
            else:
                idx = self._extract_value(node.slice)

            try:
                key = normalize_name(idx) if normalize_key and isinstance(idx, str) else idx
                return container[key]
            except Exception:
                return None
        elif isinstance(node, ast.Call):
            func_name = self._get_func_name(node)

            if func_name in ("list", "tuple") and node.args:
                inner = self._extract_value(node.args[0])
                if inner is None:
                    return None
                return list(inner) if func_name == "list" else tuple(inner)

            if func_name == "deps_list":
                lookup = self.variables.get("deps") or self._build_deps_lookup()
                items = []
                for arg in node.args:
                    val = self._extract_value(arg)
                    if isinstance(val, (list, tuple)):
                        items.extend(val)
                    elif isinstance(val, str):
                        key = normalize_name(val)
                        if lookup and key in lookup:
                            items.append(lookup[key])
                        else:
                            items.append(val)
                return items

            return None
        elif isinstance(node, ast.Name):
            return self.variables.get(node.id)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left = self._extract_value(node.left)
            right = self._extract_value(node.right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
        return None

    def _build_deps_lookup(self):
        """Reconstruct deps mapping from a `_deps` list when possible."""
        raw = self.variables.get("_deps")
        if not isinstance(raw, list):
            return None

        lookup = {}
        for spec in raw:
            if not isinstance(spec, str):
                continue
            match = re.match(r"^([a-zA-Z0-9_.-]+)", spec.strip())
            if not match:
                continue
            pkg = normalize_name(match.group(1))
            lookup[pkg] = spec
        return lookup
