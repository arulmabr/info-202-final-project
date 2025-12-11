import re
import tomli
from ..storage import Dependency, RelationType
from .requirements_parser import normalize_name


def parse_pyproject(content: str, source_pkg: str) -> list[Dependency]:
    """Parse pyproject.toml dependencies."""
    if not content:
        return []

    try:
        data = tomli.loads(content)
    except tomli.TOMLDecodeError:
        return []

    deps = []

    # PEP 621 style: [project] section
    project = data.get('project', {})

    # main dependencies
    for dep_str in project.get('dependencies', []):
        dep = parse_dep_string(dep_str, source_pkg, RelationType.REQUIRES_CORE, 'pyproject.toml')
        if dep:
            deps.append(dep)

    # optional dependencies
    for group, dep_list in project.get('optional-dependencies', {}).items():
        is_dev = group in ('dev', 'test', 'testing', 'tests', 'develop', 'docs')
        rel_type = RelationType.REQUIRES_DEV if is_dev else RelationType.REQUIRES_OPTIONAL
        for dep_str in dep_list:
            dep = parse_dep_string(dep_str, source_pkg, rel_type, f'pyproject.toml[{group}]')
            if dep:
                deps.append(dep)

    # Poetry style: [tool.poetry.dependencies]
    poetry = data.get('tool', {}).get('poetry', {})

    for pkg, spec in poetry.get('dependencies', {}).items():
        if pkg.lower() == 'python':
            continue
        dep = make_poetry_dep(pkg, spec, source_pkg, RelationType.REQUIRES_CORE, 'pyproject.toml')
        if dep:
            deps.append(dep)

    for pkg, spec in poetry.get('dev-dependencies', {}).items():
        dep = make_poetry_dep(pkg, spec, source_pkg, RelationType.REQUIRES_DEV, 'pyproject.toml')
        if dep:
            deps.append(dep)

    # Poetry groups
    for group, group_data in poetry.get('group', {}).items():
        is_dev = group in ('dev', 'test', 'docs')
        rel_type = RelationType.REQUIRES_DEV if is_dev else RelationType.REQUIRES_OPTIONAL
        for pkg, spec in group_data.get('dependencies', {}).items():
            dep = make_poetry_dep(pkg, spec, source_pkg, rel_type, f'pyproject.toml[{group}]')
            if dep:
                deps.append(dep)

    return deps


def parse_dep_string(dep_str: str, source_pkg: str, rel_type: RelationType, source_file: str) -> Dependency | None:
    """Parse PEP 508 style dependency string."""
    # strip markers
    dep_str = re.split(r'\s*;\s*', dep_str)[0].strip()

    match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?\s*(.*)?$', dep_str)
    if not match:
        return None

    pkg_name = normalize_name(match.group(1))
    version = match.group(2).strip() if match.group(2) else None

    if not pkg_name or pkg_name == source_pkg:
        return None

    return Dependency(
        source=source_pkg,
        target=pkg_name,
        relation_type=rel_type,
        version_constraint=version,
        source_file=source_file
    )


def make_poetry_dep(pkg: str, spec, source_pkg: str, rel_type: RelationType, source_file: str) -> Dependency | None:
    """Create dependency from Poetry spec (can be string or dict)."""
    pkg_name = normalize_name(pkg)

    if not pkg_name or pkg_name == source_pkg:
        return None

    version = None
    if isinstance(spec, str):
        version = spec
    elif isinstance(spec, dict):
        version = spec.get('version')
        if spec.get('optional'):
            rel_type = RelationType.REQUIRES_OPTIONAL

    return Dependency(
        source=source_pkg,
        target=pkg_name,
        relation_type=rel_type,
        version_constraint=version,
        source_file=source_file
    )
