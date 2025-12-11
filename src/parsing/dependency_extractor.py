from ..storage import Repository, Dependency
from .pyproject_parser import parse_pyproject
from .setup_parser import parse_setup_py
from .requirements_parser import parse_requirements


def extract_dependencies(repo: Repository) -> list[Dependency]:
    """Extract dependencies from all available files in a repository."""
    pkg_name = repo.package_name or repo.full_name.split('/')[-1].lower()

    deps = []
    seen = set()  # (source, target, rel_type)

    # priority order: pyproject.toml > setup.py > requirements.txt
    if repo.pyproject_toml:
        deps.extend(parse_pyproject(repo.pyproject_toml, pkg_name))

    if repo.setup_py:
        deps.extend(parse_setup_py(repo.setup_py, pkg_name))

    if repo.requirements_txt:
        deps.extend(parse_requirements(repo.requirements_txt, pkg_name, 'requirements.txt'))

    # dedupe, keeping first occurrence (higher priority source)
    unique = []
    for d in deps:
        key = (d.source, d.target, d.relation_type)
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique


def extract_all(repos: list[Repository]) -> dict[str, list[Dependency]]:
    """Extract dependencies from multiple repositories."""
    result = {}
    for repo in repos:
        pkg = repo.package_name or repo.full_name.split('/')[-1].lower()
        result[pkg] = extract_dependencies(repo)
    return result
