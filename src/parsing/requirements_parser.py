import re
from ..storage import Dependency, RelationType


def parse_requirements(content: str, source_pkg: str, source_file: str = "requirements.txt") -> list[Dependency]:
    """Parse requirements.txt format."""
    if not content:
        return []

    deps = []
    is_dev = 'dev' in source_file.lower() or 'test' in source_file.lower()

    for line in content.splitlines():
        line = line.strip()

        # skip empty, comments, options
        if not line or line.startswith('#') or line.startswith('-'):
            continue

        # handle -r includes (we don't follow them, just skip)
        if line.startswith('-r '):
            continue

        dep = parse_requirement_line(line, source_pkg, source_file, is_dev)
        if dep:
            deps.append(dep)

    return deps


def parse_requirement_line(line: str, source_pkg: str, source_file: str, is_dev: bool = False) -> Dependency | None:
    """Parse a single requirement line."""
    # remove environment markers
    line = re.split(r'\s*;\s*', line)[0].strip()

    # handle extras like package[extra1,extra2]
    match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[.*\])?\s*(.*)?$', line)
    if not match:
        return None

    pkg_name = normalize_name(match.group(1))
    version_spec = match.group(2).strip() if match.group(2) else None

    if not pkg_name or pkg_name == source_pkg:
        return None

    rel_type = RelationType.REQUIRES_DEV if is_dev else RelationType.REQUIRES_CORE

    return Dependency(
        source=source_pkg,
        target=pkg_name,
        relation_type=rel_type,
        version_constraint=version_spec,
        source_file=source_file
    )


def normalize_name(name: str) -> str:
    """Normalize package name per PEP 503."""
    return re.sub(r'[-_.]+', '-', name).lower()
