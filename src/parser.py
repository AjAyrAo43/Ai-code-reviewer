"""
Diff Parser - Parses git diffs and performs AST analysis.
"""

import re
import subprocess
import sys
from typing import Dict, List, Any, Optional
from pyflakes.api import check
from pyflakes.messages import Message
from astroid import parse as astroid_parse
from astroid.exceptions import AstroidError


class DiffParser:
    """Parser for git diffs and code analysis."""

    def __init__(self):
        """Initialize the diff parser."""
        self.file_pattern = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
        self.hunk_pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
        self.addition_pattern = re.compile(r"^\+(?!\+\+).*$", re.MULTILINE)

    def parse(self, diff: str) -> Dict[str, Any]:
        """
        Parse a git diff string into structured data.

        Args:
            diff: Raw git diff string

        Returns:
            Dictionary containing parsed diff data
        """
        files = []
        current_file = None
        current_lines = []
        current_line_number = 0

        for line in diff.split("\n"):
            # Check for new file
            file_match = self.file_pattern.search(line)
            if file_match:
                # Save previous file
                if current_file:
                    current_file["diff"] = "\n".join(current_lines)
                    files.append(current_file)

                current_file = {"path": file_match.group(1), "changes": []}
                current_lines = []
                current_line_number = 0
                continue

            # Check for hunk header
            hunk_match = self.hunk_pattern.match(line)
            if hunk_match:
                current_line_number = int(hunk_match.group(1)) - 1
                current_lines.append(line)
                continue

            # Check for addition
            if line.startswith("+") and not line.startswith("+++"):
                current_line_number += 1
                current_file["changes"].append(
                    {"line": current_line_number, "content": line[1:], "type": "addition"}
                )
                current_lines.append(line)
            elif line.startswith("-") and not line.startswith("---"):
                current_lines.append(line)
            else:
                if current_file:
                    current_lines.append(line)

        # Don't forget the last file
        if current_file:
            current_file["diff"] = "\n".join(current_lines)
            files.append(current_file)

        return {"files": files, "raw_diff": diff}

    def check_syntax(self, code: str) -> List[Dict[str, Any]]:
        """
        Check Python code for syntax errors using pyflakes.

        Args:
            code: Python code string

        Returns:
            List of issues found
        """
        issues = []
        try:
            # Capture pyflakes messages
            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            check(code, "<string>")

            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

            if output:
                issues.append({"type": "pyflakes", "message": output.strip()})
        except Exception as e:
            issues.append({"type": "syntax_error", "message": str(e)})

        return issues

    def analyze_ast(self, code: str) -> Dict[str, Any]:
        """
        Analyze Python code using AST.

        Args:
            code: Python code string

        Returns:
            AST analysis results
        """
        result = {"functions": [], "classes": [], "imports": [], "complexity": 0}

        try:
            tree = astroid_parse(code)

            for node in tree.body:
                if hasattr(node, "name"):
                    if node.__class__.__name__ == "FunctionDef":
                        result["functions"].append(
                            {
                                "name": node.name,
                                "args": [arg.name for arg in node.args.args],
                                "line": node.lineno,
                            }
                        )
                        result["complexity"] += 1
                    elif node.__class__.__name__ == "ClassDef":
                        result["classes"].append(
                            {"name": node.name, "line": node.lineno}
                        )
                        result["complexity"] += 1
                elif node.__class__.__name__ == "Import":
                    for alias in node.names:
                        result["imports"].append(alias[0])
                elif node.__class__.__name__ == "ImportFrom":
                    module = node.modname or ""
                    for alias in node.names:
                        result["imports"].append(f"{module}.{alias[0]}")

        except AstroidError:
            pass

        return result

    def parse_file_diff(self, file_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a GitHub file object from the API into a structured dict.

        Args:
            file_obj: Dict with filename, patch, status fields from GitHub API

        Returns:
            Dict with parsed diff data, or None if no patch field (binary file)
        """
        if "patch" not in file_obj:
            return None

        filename = file_obj.get("filename", "unknown")
        patch = file_obj.get("patch", "")
        status = file_obj.get("status", "modified")

        # Detect language from extension
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rb": "Ruby",
            ".cpp": "C++",
        }
        ext = "." + filename.split(".")[-1] if "." in filename else ""
        language = ext_map.get(ext, "Unknown")

        # Parse line numbers from patch
        line_number_map = self.parse_line_numbers(patch)

        # Extract added and removed lines
        added_lines = []
        removed_lines = []
        current_added_pos = 0
        current_removed_pos = 0

        for line in patch.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                current_added_pos += 1
                actual_line = line_number_map.get(current_added_pos)
                added_lines.append({
                    "line_number": actual_line,
                    "content": line[1:]
                })
            elif line.startswith("-") and not line.startswith("---"):
                current_removed_pos += 1
                removed_lines.append({
                    "line_number": current_removed_pos,
                    "content": line[1:]
                })

        # Extract chunk header (@@ line numbers @@)
        chunk_header = None
        header_match = re.search(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@", patch, re.MULTILINE)
        if header_match:
            chunk_header = header_match.group(0)

        return {
            "filename": filename,
            "language": language,
            "status": status,
            "patch": patch,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "chunk_header": chunk_header,
        }

    def parse_line_numbers(self, patch: str) -> Dict[int, int]:
        """
        Parse diff patch to build a map from diff position to actual file line number.

        The @@ -a,b +c,d @@ header tells you where lines start.
        Returns a dict {position: actual_line_number} for added lines only.

        Args:
            patch: Raw diff patch string

        Returns:
            Dict mapping position in added lines to actual file line number
        """
        line_map = {}
        added_pos = 0
        current_new_line = 0

        for line in patch.split("\n"):
            # Parse hunk header
            header_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            if header_match:
                current_new_line = int(header_match.group(1)) - 1
                continue

            # Track added lines
            if line.startswith("+") and not line.startswith("+++"):
                added_pos += 1
                current_new_line += 1
                line_map[added_pos] = current_new_line

        return line_map

    def extract_added_code(self, patch: str) -> str:
        """
        Extract only added lines from a diff patch.

        Args:
            patch: Raw diff patch string

        Returns:
            String of added lines with line numbers prepended
        """
        added_lines = []
        line_num = 0

        for line in patch.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                line_num += 1
                added_lines.append(f"{line_num}: {line[1:]}")

        return "\n".join(added_lines)

    def truncate_diff(self, patch: str, max_chars: int = 8000) -> str:
        """
        Truncate a diff patch if it exceeds max_chars.

        Keeps first 4000 and last 4000 chars with a truncation message in between.

        Args:
            patch: Raw diff patch string
            max_chars: Maximum character limit (default 8000)

        Returns:
            Truncated patch string
        """
        if len(patch) <= max_chars:
            return patch

        half_size = max_chars // 2
        truncation_message = "\n\n[... diff truncated ...]\n\n"

        first_part = patch[:half_size]
        last_part = patch[-half_size:]

        return first_part + truncation_message + last_part

    def static_analysis_python(self, code_string: str) -> List[str]:
        """
        Run pyflakes on a code string using subprocess and capture warnings.

        Args:
            code_string: Python code string to analyze

        Returns:
            List of warning strings, empty if not Python or no warnings
        """
        if not code_string.strip():
            return []

        try:
            # Run pyflakes via subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pyflakes", "-"],
                input=code_string,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Parse stdout for warnings
            warnings = []
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        warnings.append(line.strip())

            return warnings

        except subprocess.TimeoutExpired:
            return ["pyflakes analysis timed out"]
        except Exception:
            return []


def build_review_payload(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build a clean list of parsed file objects ready for LLM review.

    Takes a list of file objects from GitHub API, parses each one,
    filters out binary files (no patch field), and returns parsed data.

    Args:
        files: List of file objects from GitHub API

    Returns:
        List of parsed file dicts ready for review
    """
    parser = DiffParser()
    payload = []

    for file_obj in files:
        parsed = parser.parse_file_diff(file_obj)
        if parsed is not None:
            payload.append(parsed)

    return payload
