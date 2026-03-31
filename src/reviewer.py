"""
Code Reviewer - Uses Groq API to analyze code changes.
"""

from groq import Groq
from typing import Dict, List, Any


class CodeReviewer:
    """Code reviewer powered by Groq API."""

    def __init__(self, api_key: str):
        """
        Initialize the code reviewer.

        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        self.model = "meta-llama/llama-4-maverick-17b-128e-instruct"

    def review(self, parsed_diff: Dict[str, Any], pr_data: Dict[str, Any], files_with_analysis: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Review code changes using Groq.

        Args:
            parsed_diff: Parsed diff data from DiffParser
            pr_data: Pull request metadata
            files_with_analysis: Optional list of files with static analysis results

        Returns:
            Review results with comments and feedback
        """
        prompt = self._build_review_prompt(parsed_diff, pr_data, files_with_analysis)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=4096,
        )

        return self._parse_review_response(response.choices[0].message.content)

    def _build_review_prompt(
        self, parsed_diff: Dict[str, Any], pr_data: Dict[str, Any], files_with_analysis: List[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for Claude to review the code."""
        pr_title = pr_data.get("title", "Untitled PR")
        pr_description = pr_data.get("body", "No description provided")

        diff_content = "\n\n".join(
            [f"File: {f['path']}\n{f['diff']}" for f in parsed_diff.get("files", [])]
        )

        # Build static analysis section
        static_analysis_section = ""
        if files_with_analysis:
            analysis_parts = []
            for file_info in files_with_analysis:
                if "lint_warnings" in file_info and file_info["lint_warnings"]:
                    analysis_parts.append(
                        f"**{file_info['filename']}** ({file_info['language']}):\n"
                        + "\n".join(f"  - {w}" for w in file_info["lint_warnings"])
                    )
            if analysis_parts:
                static_analysis_section = "\n\n### Static Analysis Warnings\n\n" + "\n\n".join(analysis_parts)

        return f"""You are an expert code reviewer. Analyze the following pull request and provide detailed feedback.

## Pull Request: {pr_title}

### Description
{pr_description}

### Code Changes
{diff_content}{static_analysis_section}

Please review the code changes and provide:

1. **Overall Assessment**: A brief summary of the changes and their quality.

2. **Issues Found**: Any bugs, security vulnerabilities, performance issues, or code quality problems.
   - Pay special attention to any Static Analysis Warnings listed above - these are automated findings that likely indicate real issues.

3. **Suggestions**: Specific suggestions for improvement with code examples where applicable.

4. **Inline Comments**: For specific problematic lines, indicate the file path, line number, and suggested comment.

Format your response as JSON with this structure:
{{
    "overall_assessment": "...",
    "issues": ["issue 1", "issue 2"],
    "suggestions": ["suggestion 1", "suggestion 2"],
    "inline_comments": [
        {{"file": "path/to/file.py", "line": 42, "comment": "Suggestion text"}}
    ]
}}

Respond with valid JSON only."""

    def _parse_review_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's review response into structured data."""
        import json

        # Extract JSON from the response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            return {
                "overall_assessment": response_text,
                "issues": [],
                "suggestions": [],
                "inline_comments": [],
            }

        try:
            return json.loads(response_text[start_idx:end_idx])
        except json.JSONDecodeError:
            return {
                "overall_assessment": response_text,
                "issues": [],
                "suggestions": [],
                "inline_comments": [],
            }
