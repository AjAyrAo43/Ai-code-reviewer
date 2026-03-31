# Project: AI Code Review Agent
## Goal
Autonomous GitHub PR reviewer using Groq API — reads diffs, posts inline comments with bugs/security issues/suggestions.

## Current status
- [x] Phase 1: Project structure & setup
- [x] Phase 2: GitHub API client (github_client.py)
- [x] Phase 3: Diff parser & static analysis (parser.py)
- [x] Phase 4: Groq LLM reviewer (reviewer.py)
- [x] Phase 4B: Comment poster (commenter.py)
- [x] Phase 5: Main entry point (main.py)
- [x] Phase 6: GitHub Actions & Dockerfile
- [ ] Phase 7: Local test script (test_local.py)
- [ ] Phase 8: Final polish & retry logic

## Files created so far
- src/main.py - Entry point
- src/github_client.py - GitHub API client
- src/parser.py - Diff parser
- src/reviewer.py - Groq-powered code reviewer
- src/commenter.py - PR comment poster
- .github/workflows/review.yml - GitHub Actions workflow
- Dockerfile
- requirements.txt
- .env.example - Environment variable template
- .gitignore

## Key decisions made
- Language: Python 3.11
- LLM: Groq API (meta-llama/llama-4-maverick-17b-128e-instruct model)
- GitHub integration: REST API via requests library
- Output format: Inline PR comments + overall summary
- CI/CD: GitHub Actions triggered on PR open/update

## Dependencies
groq, requests, python-dotenv, pyflakes, astroid

## Env vars needed
GROQ_API_KEY, GITHUB_TOKEN, GITHUB_REPO, PR_NUMBER

## Last session ended at
Session 2 - Migrated from Anthropic to Groq API, added .gitignore

## Notes / issues to fix next session
- Add actual GROQ_API_KEY value to .env file for testing
