from ..storage import Dependency, RelationType


# Packages that indicate dev dependencies regardless of where they appear
DEV_PACKAGES = {
    'pytest', 'pytest-cov', 'pytest-xdist', 'pytest-asyncio',
    'black', 'ruff', 'flake8', 'pylint', 'mypy', 'isort',
    'pre-commit', 'tox', 'nox', 'coverage',
    'sphinx', 'mkdocs', 'pdoc',
    'twine', 'build', 'wheel', 'setuptools',
    'ipdb', 'pdb', 'debugpy',
}

# Known extension/wrapper patterns
EXTENSION_PATTERNS = {
    'torch': ['pytorch-lightning', 'torch-geometric', 'torchvision', 'torchaudio', 'torchtext'],
    'tensorflow': ['tf-keras', 'tensorflow-hub', 'tensorflow-datasets'],
    'sklearn': ['scikit-image', 'scikit-optimize'],
    'transformers': ['peft', 'accelerate', 'datasets'],
}


def infer_relation_type(dep: Dependency) -> RelationType:
    """Refine relation type based on package characteristics."""
    target = dep.target.lower()

    # already classified as dev
    if dep.relation_type == RelationType.REQUIRES_DEV:
        return RelationType.REQUIRES_DEV

    # known dev packages should be dev
    if target in DEV_PACKAGES:
        return RelationType.REQUIRES_DEV

    # check if it's an extension
    for base, extensions in EXTENSION_PATTERNS.items():
        if target in extensions or target.startswith(f'{base}-') or target.startswith(f'{base}_'):
            return RelationType.EXTENDS

    return dep.relation_type


def refine_dependencies(deps: list[Dependency]) -> list[Dependency]:
    """Apply inference rules to refine dependency relation types."""
    refined = []
    for dep in deps:
        new_type = infer_relation_type(dep)
        if new_type != dep.relation_type:
            dep = Dependency(
                source=dep.source,
                target=dep.target,
                relation_type=new_type,
                version_constraint=dep.version_constraint,
                source_file=dep.source_file,
                is_transitive=dep.is_transitive
            )
        refined.append(dep)
    return refined
