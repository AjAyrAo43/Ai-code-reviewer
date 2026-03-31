"""
AI Code Reviewer - Entry Point

Autonomous GitHub PR code review agent powered by Claude.
"""

import os
from dotenv import load_dotenv

from github_client import GitHubClient
from reviewer import CodeReviewer
from parser import DiffParser
from commenter import PRCommenter


def main():
    """Main entry point for the AI code reviewer."""
    load_dotenv()

    # Validate required environment variables
    required_vars = ["GROQ_API_KEY", "GITHUB_TOKEN", "GITHUB_REPO", "PR_NUMBER"]
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    pr_number = int(os.getenv("PR_NUMBER"))
    groq_api_key = os.getenv("GROQ_API_KEY")

    # Initialize components
    github_client = GitHubClient(github_token, repo)
    diff_parser = DiffParser()
    reviewer = CodeReviewer(groq_api_key)
    commenter = PRCommenter(github_client)

    # Fetch PR data
    pr_data = github_client.get_pr(pr_number)
    files = github_client.get_pr_files(pr_number)
    diff = github_client.get_pr_diff(pr_number)

    # Parse the diff
    parsed_diff = diff_parser.parse(diff)

    # Review the code
    review = reviewer.review(parsed_diff, pr_data)

    # Post comments
    commenter.post_comments(pr_number, review)

    print(f"Review complete for PR #{pr_number}")


if __name__ == "__main__":
    main()
