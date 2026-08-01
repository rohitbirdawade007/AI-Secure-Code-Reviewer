"""
github_service.py
-----------------
Fetches raw Python file content from GitHub given a blob URL.

Supported URL formats:
  - https://github.com/owner/repo/blob/branch/path/to/file.py
  - https://raw.githubusercontent.com/owner/repo/branch/path/to/file.py
"""

import re
import logging
import requests
from pathlib import PurePosixPath
from typing import Tuple

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GITHUB_BLOB_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<branch>[^/]+)/(?P<path>.+)"
)
RAW_GITHUB_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?P<branch>[^/]+)/(?P<path>.+)"
)


def _parse_github_url(url: str) -> Tuple[str, str, str, str]:
    """
    Parse a GitHub blob URL into (owner, repo, branch, file_path).

    Raises:
        ValueError: If the URL cannot be parsed.
    """
    for pattern in (GITHUB_BLOB_PATTERN, RAW_GITHUB_PATTERN):
        m = pattern.match(url.strip())
        if m:
            return m.group("owner"), m.group("repo"), m.group("branch"), m.group("path")
    raise ValueError(
        f"Unrecognized GitHub URL format: {url}\n"
        "Expected: https://github.com/owner/repo/blob/branch/path/to/file.py"
    )


def _build_raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def fetch_github_file(url: str) -> Tuple[str, str]:
    """
    Download a single file from GitHub and return its content + filename.

    Args:
        url: GitHub blob or raw URL.

    Returns:
        Tuple of (file_content: str, filename: str).

    Raises:
        ValueError: On bad URL format.
        RuntimeError: On HTTP errors or non-Python files.
    """
    owner, repo, branch, path = _parse_github_url(url)

    # Enforce Python files only
    suffix = PurePosixPath(path).suffix.lower()
    if suffix != ".py":
        raise RuntimeError(
            f"Only Python (.py) files are supported. Got: {suffix or '(no extension)'}"
        )

    raw_url = _build_raw_url(owner, repo, branch, path)
    filename = PurePosixPath(path).name

    headers = {"Accept": "application/vnd.github.v3.raw"}
    if settings.github_token:
        headers["Authorization"] = f"token {settings.github_token}"

    logger.info("Fetching GitHub file: %s", raw_url)

    response = requests.get(raw_url, headers=headers, timeout=15)

    if response.status_code == 404:
        raise RuntimeError(
            f"File not found on GitHub: {raw_url}\n"
            "Make sure the repository is public and the path/branch is correct."
        )
    if response.status_code == 403:
        raise RuntimeError(
            "GitHub rate limit exceeded or access denied. "
            "Set GITHUB_TOKEN in .env to increase rate limits."
        )
    if not response.ok:
        raise RuntimeError(
            f"GitHub API error {response.status_code}: {response.text[:200]}"
        )

    content = response.text
    logger.info("Fetched %d bytes from GitHub (%s).", len(content), filename)
    return content, filename
