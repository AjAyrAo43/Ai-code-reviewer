# AI Code Reviewer

An autonomous GitHub PR code review agent powered by Claude that automatically reviews GitHub pull requests and posts inline comments.

## Features

- Automatically fetches PR diffs from GitHub
- Uses Claude API to analyze code changes
- Posts inline comments on PRs with suggestions and feedback
- Runs as a GitHub Action or standalone Docker container

## Setup

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the reviewer:
   ```bash
   python src/main.py
   ```

## Configuration

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GITHUB_TOKEN`: GitHub personal access token with repo scope
- `GITHUB_REPO`: Repository in format `owner/repo`
- `PR_NUMBER`: Pull request number to review

## License

MIT
# Ai-code-reviewer
