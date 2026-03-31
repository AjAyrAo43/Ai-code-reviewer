"""
AI Code Reviewer - Entry Point

Autonomous GitHub PR code review agent powered by Claude.
"""

import os
from dotenv import load_dotenv

from github_client import GitHubClient
from reviewer import CodeReviewer
from parser import DiffParser, build_review_payload
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

    # Parse the diff and run static analysis
    parsed_diff = diff_parser.parse(diff)
    files_with_analysis = build_review_payload(files, run_static_analysis=True)

    # Review the code (pass both parsed diff and static analysis results)
    review = reviewer.review(parsed_diff, pr_data, files_with_analysis)

    # Post comments
    commenter.post_comments(pr_number, review)

    print(f"Review complete for PR #{pr_number}")


if __name__ == "__main__":
    main()
