"""
Diff Parser - Parses git diffs and performs AST analysis.
"""

import re
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
