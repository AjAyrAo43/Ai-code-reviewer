"""
PR Commenter - Posts inline comments on GitHub PRs.
"""

from typing import Dict, List, Any
from github_client import GitHubClient


class PRCommenter:
    """Handles posting comments on pull requests."""

    def __init__(self, github_client: GitHubClient):
        """
        Initialize the PR commenter.

        Args:
            github_client: GitHubClient instance
        """
        self.github_client = github_client

    def post_comments(
        self, pr_number: int, review: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Post all review comments to a pull request.

        Args:
            pr_number: The pull request number
            review: Review data from CodeReviewer

        Returns:
            List of posted comments
        """
        posted_comments = []

        # Post inline comments for specific lines
        inline_comments = review.get("inline_comments", [])
        for comment in inline_comments:
            try:
                # Get the commit SHA (using PR head for simplicity)
                pr_data = self.github_client.get_pr(pr_number)
                commit_sha = pr_data["head"]["sha"]

                result = self.github_client.post_comment(
                    pr_number=pr_number,
                    commit_sha=commit_sha,
                    path=comment["file"],
                    line=comment["line"],
                    body=comment["comment"],
                )
                posted_comments.append(result)
            except Exception as e:
                print(f"Failed to post inline comment: {e}")

        # Post summary comment if there are issues or suggestions
        issues = review.get("issues", [])
        suggestions = review.get("suggestions", [])
        overall = review.get("overall_assessment", "")

        if issues or suggestions or overall:
            summary = self._build_summary(review)
            try:
                result = self.github_client.post_review_comment(
                    pr_number=pr_number,
                    body=summary,
                )
                posted_comments.append(result)
            except Exception as e:
                print(f"Failed to post summary comment: {e}")

        return posted_comments

    def _build_summary(self, review: Dict[str, Any]) -> str:
        """Build a summary comment from the review."""
        lines = []

        overall = review.get("overall_assessment", "")
        if overall:
            lines.append("## Code Review Summary\n")
            lines.append(overall)
            lines.append("")

        issues = review.get("issues", [])
        if issues:
            lines.append("### Issues Found\n")
            for issue in issues:
                lines.append(f"- {issue}")
            lines.append("")

        suggestions = review.get("suggestions", [])
        if suggestions:
            lines.append("### Suggestions\n")
            for suggestion in suggestions:
                lines.append(f"- {suggestion}")

        return "\n".join(lines)
