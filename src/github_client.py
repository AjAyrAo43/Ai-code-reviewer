"""
GitHub Client - Handles interactions with the GitHub API.
"""

import requests
from typing import Dict, List, Any


class GitHubClient:
    """Client for interacting with the GitHub API."""

    def __init__(self, token: str, repo: str):
        """
        Initialize the GitHub client.

        Args:
            token: GitHub personal access token
            repo: Repository in format 'owner/repo'
        """
        self.token = token
        self.owner, self.repo_name = repo.split("/")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make a GET request to the GitHub API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the GitHub API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_pr(self, pr_number: int) -> Dict[str, Any]:
        """
        Fetch pull request details.

        Args:
            pr_number: The pull request number

        Returns:
            PR data including title, description, and state
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}"
        return self._get(endpoint)

    def get_pr_files(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch files changed in a pull request.

        Args:
            pr_number: The pull request number

        Returns:
            List of changed files with metadata
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/files"
        return self._get(endpoint)

    def get_pr_diff(self, pr_number: int) -> str:
        """
        Fetch the raw diff of a pull request.

        Args:
            pr_number: The pull request number

        Returns:
            Raw diff string
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}"
        url = f"{self.base_url}{endpoint}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def post_comment(self, pr_number: int, commit_sha: str, path: str, line: int, body: str) -> Dict[str, Any]:
        """
        Post an inline comment on a pull request.

        Args:
            pr_number: The pull request number
            commit_sha: The commit SHA to comment on
            path: File path
            line: Line number
            body: Comment body

        Returns:
            Created comment data
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/comments"
        data = {
            "body": body,
            "commit_id": commit_sha,
            "path": path,
            "line": line,
        }
        return self._post(endpoint, data)

    def post_review_comment(self, pr_number: int, body: str) -> Dict[str, Any]:
        """
        Post a general comment on a pull request review.

        Args:
            pr_number: The pull request number
            body: Comment body

        Returns:
            Created comment data
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/comments"
        data = {"body": body}
        return self._post(endpoint, data)
