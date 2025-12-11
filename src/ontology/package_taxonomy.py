from datetime import datetime, timedelta, timezone
from ..storage import Package, Domain, Role, HealthStatus


# Manual classifications for well-known packages
KNOWN_PACKAGES = {
    # Deep Learning
    'torch': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
    'pytorch': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
    'tensorflow': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
    'jax': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
    'keras': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
    'flax': (Domain.DEEP_LEARNING, Role.LIBRARY),
    'pytorch-lightning': (Domain.DEEP_LEARNING, Role.EXTENSION),
    'lightning': (Domain.DEEP_LEARNING, Role.EXTENSION),
    'fastai': (Domain.DEEP_LEARNING, Role.EXTENSION),

    # Traditional ML
    'scikit-learn': (Domain.TRADITIONAL_ML, Role.FRAMEWORK),
    'sklearn': (Domain.TRADITIONAL_ML, Role.FRAMEWORK),
    'xgboost': (Domain.TRADITIONAL_ML, Role.LIBRARY),
    'lightgbm': (Domain.TRADITIONAL_ML, Role.LIBRARY),
    'catboost': (Domain.TRADITIONAL_ML, Role.LIBRARY),

    # Data Processing
    'pandas': (Domain.DATA_PROCESSING, Role.FRAMEWORK),
    'numpy': (Domain.DATA_PROCESSING, Role.FRAMEWORK),
    'polars': (Domain.DATA_PROCESSING, Role.FRAMEWORK),
    'dask': (Domain.DATA_PROCESSING, Role.FRAMEWORK),
    'scipy': (Domain.DATA_PROCESSING, Role.LIBRARY),
    'pyarrow': (Domain.DATA_PROCESSING, Role.LIBRARY),
    'h5py': (Domain.DATA_PROCESSING, Role.LIBRARY),

    # Visualization
    'matplotlib': (Domain.VISUALIZATION, Role.FRAMEWORK),
    'plotly': (Domain.VISUALIZATION, Role.FRAMEWORK),
    'seaborn': (Domain.VISUALIZATION, Role.LIBRARY),
    'altair': (Domain.VISUALIZATION, Role.LIBRARY),
    'bokeh': (Domain.VISUALIZATION, Role.FRAMEWORK),

    # NLP
    'transformers': (Domain.NLP, Role.FRAMEWORK),
    'spacy': (Domain.NLP, Role.FRAMEWORK),
    'nltk': (Domain.NLP, Role.LIBRARY),
    'tokenizers': (Domain.NLP, Role.LIBRARY),
    'sentencepiece': (Domain.NLP, Role.LIBRARY),
    'tiktoken': (Domain.NLP, Role.LIBRARY),

    # Computer Vision
    'opencv-python': (Domain.COMPUTER_VISION, Role.FRAMEWORK),
    'cv2': (Domain.COMPUTER_VISION, Role.FRAMEWORK),
    'pillow': (Domain.COMPUTER_VISION, Role.LIBRARY),
    'pil': (Domain.COMPUTER_VISION, Role.LIBRARY),
    'torchvision': (Domain.COMPUTER_VISION, Role.EXTENSION),
    'albumentations': (Domain.COMPUTER_VISION, Role.LIBRARY),

    # Utilities
    'tqdm': (Domain.UTILITIES, Role.LIBRARY),
    'requests': (Domain.UTILITIES, Role.LIBRARY),
    'pyyaml': (Domain.UTILITIES, Role.LIBRARY),
    'pydantic': (Domain.UTILITIES, Role.LIBRARY),
    'click': (Domain.UTILITIES, Role.LIBRARY),
    'typer': (Domain.UTILITIES, Role.LIBRARY),
    'rich': (Domain.UTILITIES, Role.LIBRARY),

    # Infrastructure / Tools
    'pytest': (Domain.INFRASTRUCTURE, Role.TOOL),
    'black': (Domain.INFRASTRUCTURE, Role.TOOL),
    'ruff': (Domain.INFRASTRUCTURE, Role.TOOL),
    'mypy': (Domain.INFRASTRUCTURE, Role.TOOL),
    'pip': (Domain.INFRASTRUCTURE, Role.TOOL),
    'setuptools': (Domain.INFRASTRUCTURE, Role.LIBRARY),

    # ML Tools
    'wandb': (Domain.DEEP_LEARNING, Role.TOOL),
    'mlflow': (Domain.DEEP_LEARNING, Role.TOOL),
    'optuna': (Domain.TRADITIONAL_ML, Role.TOOL),
    'ray': (Domain.DEEP_LEARNING, Role.FRAMEWORK),
}

# Pattern-based domain inference
DOMAIN_PATTERNS = {
    Domain.DEEP_LEARNING: ['torch', 'tensorflow', 'tf-', 'keras', 'neural', 'nn-'],
    Domain.NLP: ['nlp', 'text', 'language', 'token', 'bert', 'gpt', 'llm'],
    Domain.COMPUTER_VISION: ['vision', 'image', 'cv', 'detection', 'segmentation'],
    Domain.VISUALIZATION: ['plot', 'chart', 'graph', 'vis', 'draw'],
    Domain.DATA_PROCESSING: ['data', 'pandas', 'array', 'table', 'csv', 'parquet'],
}


def classify_package(pkg: Package) -> Package:
    """Assign domain and role to a package."""
    name = pkg.name.lower()

    # check known packages first
    if name in KNOWN_PACKAGES:
        domain, role = KNOWN_PACKAGES[name]
        pkg.domain = domain.value
        pkg.role = role.value
        return pkg

    # pattern matching
    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in name:
                pkg.domain = domain.value
                break

    # role inference based on name
    if name.endswith('-cli') or name.endswith('-tool'):
        pkg.role = Role.TOOL.value
    elif any(name.startswith(f'{fw}-') or name.endswith(f'-{fw}') for fw in ['torch', 'tf', 'sklearn']):
        pkg.role = Role.EXTENSION.value

    return pkg


def assess_health(pkg: Package) -> Package:
    """Assess package health based on activity."""
    if not pkg.last_commit_date:
        pkg.health_status = HealthStatus.UNKNOWN.value
        return pkg

    now = datetime.now(timezone.utc)
    age = now - pkg.last_commit_date

    if age < timedelta(days=90):
        pkg.health_status = HealthStatus.ACTIVE.value
    elif age < timedelta(days=365):
        pkg.health_status = HealthStatus.STABLE.value
    else:
        pkg.health_status = HealthStatus.DECLINING.value

    return pkg


def classify_and_assess(pkg: Package) -> Package:
    """Apply both classification and health assessment."""
    pkg = classify_package(pkg)
    pkg = assess_health(pkg)
    return pkg
