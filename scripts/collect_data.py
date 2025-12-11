#!/usr/bin/env python3
"""Collect repository data from GitHub."""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file before any other imports that might use env vars
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collection import GitHubClient, RepoFetcher, get_seed_repos
from src.storage import Database


def main():
    client = GitHubClient()
    db = Database()
    fetcher = RepoFetcher(client, db)

    # check rate limit
    remaining = client.remaining_requests()
    print(f"GitHub API requests remaining: {remaining}")

    if remaining < 100:
        print("Warning: Low rate limit. Consider waiting or using a token.")

    repos = get_seed_repos()
    print(f"Collecting data from {len(repos)} repositories...")

    fetcher.fetch_all(repos)

    print(f"\nDone. Data stored in {db.db_path}")


if __name__ == "__main__":
    main()
