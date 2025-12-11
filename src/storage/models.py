from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class RelationType(Enum):
    REQUIRES_CORE = "requires_core"
    REQUIRES_OPTIONAL = "requires_optional"
    REQUIRES_DEV = "requires_dev"
    EXTENDS = "extends"


class Domain(Enum):
    DEEP_LEARNING = "deep_learning"
    TRADITIONAL_ML = "traditional_ml"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    UTILITIES = "utilities"
    INFRASTRUCTURE = "infrastructure"


class Role(Enum):
    FRAMEWORK = "framework"
    LIBRARY = "library"
    TOOL = "tool"
    EXTENSION = "extension"


class HealthStatus(Enum):
    ACTIVE = "active"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


@dataclass
class Package:
    name: str
    github_repo: str | None = None
    domain: str = Domain.UTILITIES.value
    role: str = Role.LIBRARY.value
    health_status: str = HealthStatus.UNKNOWN.value
    description: str | None = None
    latest_version: str | None = None
    github_stars: int | None = None
    last_commit_date: datetime | None = None

    in_degree: int = 0
    out_degree: int = 0
    pagerank: float = 0.0
    betweenness: float = 0.0

    def to_dict(self):
        d = asdict(self)
        if d['last_commit_date']:
            d['last_commit_date'] = d['last_commit_date'].isoformat()
        return d

    @classmethod
    def from_dict(cls, d):
        if d.get('last_commit_date') and isinstance(d['last_commit_date'], str):
            d['last_commit_date'] = datetime.fromisoformat(d['last_commit_date'])
        return cls(**d)


@dataclass
class Dependency:
    source: str
    target: str
    relation_type: RelationType
    version_constraint: str | None = None
    source_file: str = ""
    is_transitive: bool = False

    def to_dict(self):
        d = asdict(self)
        d['relation_type'] = self.relation_type.value
        return d

    @classmethod
    def from_dict(cls, d):
        d['relation_type'] = RelationType(d['relation_type'])
        return cls(**d)


@dataclass
class Repository:
    full_name: str  # owner/repo
    stars: int = 0
    description: str | None = None
    last_commit: datetime | None = None
    default_branch: str = "main"
    package_name: str | None = None  # associated PyPI package if known

    # raw file contents cached
    pyproject_toml: str | None = None
    setup_py: str | None = None
    requirements_txt: str | None = None
    setup_cfg: str | None = None
