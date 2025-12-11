import os
import time
from functools import wraps

from github import Github, GithubException, RateLimitExceededException


def with_retry(max_retries=3, backoff=2):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except RateLimitExceededException as e:
                    reset_time = e.headers.get("x-ratelimit-reset")
                    if reset_time:
                        wait = int(reset_time) - int(time.time()) + 5
                        print(f"Rate limited. Waiting {wait}s...")
                        time.sleep(max(wait, 60))
                    else:
                        time.sleep(60)
                    last_exc = e
                except GithubException as e:
                    if e.status in (403, 500, 502, 503):
                        wait = backoff**attempt
                        print(f"GitHub error {e.status}, retrying in {wait}s...")
                        time.sleep(wait)
                        last_exc = e
                    else:
                        raise
            raise last_exc

        return wrapper

    return decorator


class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("Warning: No GITHUB_TOKEN set. Rate limits will be very low.")
        self.gh = Github(self.token) if self.token else Github()

    @with_retry()
    def get_repo(self, full_name: str):
        return self.gh.get_repo(full_name)

    @with_retry()
    def get_file_content(self, repo, path: str) -> str | None:
        try:
            content = repo.get_contents(path)
            if isinstance(content, list):
                return None  # it's a directory
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def remaining_requests(self) -> int:
        rate_limit = self.gh.get_rate_limit()
        # handle different PyGithub versions
        try:
            return rate_limit.core.remaining
        except AttributeError:
            pass
        try:
            return rate_limit.rate.remaining
        except AttributeError:
            # Fallback: access the raw rate limit data
            return self.gh.rate_limiting[0]
