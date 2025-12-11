import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager

from .models import Package, Dependency, Repository, RelationType


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.environ.get('DATABASE_PATH', 'data/ml_analyzer.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS repositories (
                    full_name TEXT PRIMARY KEY,
                    stars INTEGER,
                    description TEXT,
                    last_commit TEXT,
                    default_branch TEXT,
                    package_name TEXT,
                    pyproject_toml TEXT,
                    setup_py TEXT,
                    requirements_txt TEXT,
                    setup_cfg TEXT
                );

                CREATE TABLE IF NOT EXISTS packages (
                    name TEXT PRIMARY KEY,
                    github_repo TEXT,
                    domain TEXT,
                    role TEXT,
                    health_status TEXT,
                    description TEXT,
                    latest_version TEXT,
                    github_stars INTEGER,
                    last_commit_date TEXT,
                    in_degree INTEGER DEFAULT 0,
                    out_degree INTEGER DEFAULT 0,
                    pagerank REAL DEFAULT 0,
                    betweenness REAL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    target TEXT,
                    relation_type TEXT,
                    version_constraint TEXT,
                    source_file TEXT,
                    is_transitive INTEGER DEFAULT 0,
                    UNIQUE(source, target, relation_type)
                );

                CREATE INDEX IF NOT EXISTS idx_dep_source ON dependencies(source);
                CREATE INDEX IF NOT EXISTS idx_dep_target ON dependencies(target);
            ''')

    def save_repository(self, repo: Repository):
        with self._conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO repositories
                (full_name, stars, description, last_commit, default_branch,
                 package_name, pyproject_toml, setup_py, requirements_txt, setup_cfg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo.full_name, repo.stars, repo.description,
                repo.last_commit.isoformat() if repo.last_commit else None,
                repo.default_branch, repo.package_name,
                repo.pyproject_toml, repo.setup_py, repo.requirements_txt, repo.setup_cfg
            ))

    def get_repository(self, full_name: str) -> Repository | None:
        with self._conn() as conn:
            row = conn.execute(
                'SELECT * FROM repositories WHERE full_name = ?', (full_name,)
            ).fetchone()
            if not row:
                return None
            return Repository(
                full_name=row['full_name'],
                stars=row['stars'] or 0,
                description=row['description'],
                last_commit=datetime.fromisoformat(row['last_commit']) if row['last_commit'] else None,
                default_branch=row['default_branch'] or 'main',
                package_name=row['package_name'],
                pyproject_toml=row['pyproject_toml'],
                setup_py=row['setup_py'],
                requirements_txt=row['requirements_txt'],
                setup_cfg=row['setup_cfg']
            )

    def get_all_repositories(self) -> list[Repository]:
        with self._conn() as conn:
            rows = conn.execute('SELECT * FROM repositories').fetchall()
            return [Repository(
                full_name=r['full_name'],
                stars=r['stars'] or 0,
                description=r['description'],
                last_commit=datetime.fromisoformat(r['last_commit']) if r['last_commit'] else None,
                default_branch=r['default_branch'] or 'main',
                package_name=r['package_name'],
                pyproject_toml=r['pyproject_toml'],
                setup_py=r['setup_py'],
                requirements_txt=r['requirements_txt'],
                setup_cfg=r['setup_cfg']
            ) for r in rows]

    def save_package(self, pkg: Package):
        with self._conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO packages
                (name, github_repo, domain, role, health_status, description,
                 latest_version, github_stars, last_commit_date,
                 in_degree, out_degree, pagerank, betweenness)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pkg.name, pkg.github_repo, pkg.domain, pkg.role, pkg.health_status,
                pkg.description, pkg.latest_version, pkg.github_stars,
                pkg.last_commit_date.isoformat() if pkg.last_commit_date else None,
                pkg.in_degree, pkg.out_degree, pkg.pagerank, pkg.betweenness
            ))

    def get_package(self, name: str) -> Package | None:
        with self._conn() as conn:
            row = conn.execute('SELECT * FROM packages WHERE name = ?', (name,)).fetchone()
            if not row:
                return None
            return Package(
                name=row['name'],
                github_repo=row['github_repo'],
                domain=row['domain'],
                role=row['role'],
                health_status=row['health_status'],
                description=row['description'],
                latest_version=row['latest_version'],
                github_stars=row['github_stars'],
                last_commit_date=datetime.fromisoformat(row['last_commit_date']) if row['last_commit_date'] else None,
                in_degree=row['in_degree'],
                out_degree=row['out_degree'],
                pagerank=row['pagerank'],
                betweenness=row['betweenness']
            )

    def get_all_packages(self) -> list[Package]:
        with self._conn() as conn:
            rows = conn.execute('SELECT * FROM packages').fetchall()
            return [Package(
                name=r['name'],
                github_repo=r['github_repo'],
                domain=r['domain'],
                role=r['role'],
                health_status=r['health_status'],
                description=r['description'],
                latest_version=r['latest_version'],
                github_stars=r['github_stars'],
                last_commit_date=datetime.fromisoformat(r['last_commit_date']) if r['last_commit_date'] else None,
                in_degree=r['in_degree'],
                out_degree=r['out_degree'],
                pagerank=r['pagerank'],
                betweenness=r['betweenness']
            ) for r in rows]

    def save_dependency(self, dep: Dependency):
        with self._conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO dependencies
                (source, target, relation_type, version_constraint, source_file, is_transitive)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                dep.source, dep.target, dep.relation_type.value,
                dep.version_constraint, dep.source_file, int(dep.is_transitive)
            ))

    def save_dependencies(self, deps: list[Dependency]):
        with self._conn() as conn:
            conn.executemany('''
                INSERT OR REPLACE INTO dependencies
                (source, target, relation_type, version_constraint, source_file, is_transitive)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [(d.source, d.target, d.relation_type.value,
                   d.version_constraint, d.source_file, int(d.is_transitive)) for d in deps])

    def get_dependencies(self, source: str = None, target: str = None) -> list[Dependency]:
        with self._conn() as conn:
            if source and target:
                rows = conn.execute(
                    'SELECT * FROM dependencies WHERE source = ? AND target = ?',
                    (source, target)
                ).fetchall()
            elif source:
                rows = conn.execute(
                    'SELECT * FROM dependencies WHERE source = ?', (source,)
                ).fetchall()
            elif target:
                rows = conn.execute(
                    'SELECT * FROM dependencies WHERE target = ?', (target,)
                ).fetchall()
            else:
                rows = conn.execute('SELECT * FROM dependencies').fetchall()

            return [Dependency(
                source=r['source'],
                target=r['target'],
                relation_type=RelationType(r['relation_type']),
                version_constraint=r['version_constraint'],
                source_file=r['source_file'],
                is_transitive=bool(r['is_transitive'])
            ) for r in rows]

    def get_all_dependencies(self) -> list[Dependency]:
        return self.get_dependencies()
