from datetime import datetime

from .github_client import GitHubClient
from ..storage import Repository, Database


DEP_FILES = [
    'pyproject.toml',
    'setup.py',
    'requirements.txt',
    'setup.cfg',
]


class RepoFetcher:
    def __init__(self, client: GitHubClient = None, db: Database = None):
        self.client = client or GitHubClient()
        self.db = db or Database()

    def fetch(self, full_name: str, force: bool = False) -> Repository:
        # check cache first
        if not force:
            cached = self.db.get_repository(full_name)
            if cached and cached.pyproject_toml is not None:
                return cached

        repo = self.client.get_repo(full_name)

        # get last commit date
        commits = list(repo.get_commits()[:1])
        last_commit = commits[0].commit.committer.date if commits else None

        # try to infer package name from repo name
        pkg_name = repo.name.lower().replace('-', '_').replace('.', '_')

        result = Repository(
            full_name=full_name,
            stars=repo.stargazers_count,
            description=repo.description,
            last_commit=last_commit,
            default_branch=repo.default_branch,
            package_name=pkg_name,
        )

        # fetch dependency files
        result.pyproject_toml = self.client.get_file_content(repo, 'pyproject.toml')
        result.setup_py = self.client.get_file_content(repo, 'setup.py')
        result.requirements_txt = self.client.get_file_content(repo, 'requirements.txt')
        result.setup_cfg = self.client.get_file_content(repo, 'setup.cfg')

        self.db.save_repository(result)
        return result

    def fetch_all(self, repo_names: list[str], force: bool = False) -> list[Repository]:
        results = []
        for i, name in enumerate(repo_names):
            print(f"[{i+1}/{len(repo_names)}] Fetching {name}...")
            try:
                results.append(self.fetch(name, force=force))
            except Exception as e:
                print(f"  Error: {e}")
        return results
