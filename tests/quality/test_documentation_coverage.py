"""Documentation coverage tests — all public APIs must have docstrings.

Enforces Clean Code rule: code should explain WHY through naming and docs.
Every public class, method, and function in the src tree must have a docstring.
"""

import ast
from pathlib import Path

import pytest

SRC_PATH = Path(__file__).parent.parent.parent / "src" / "fluxdrive"

_EXCLUDED_MODULES = {"__init__.py"}


def _python_files(path: Path) -> list[Path]:
    """Collect all .py files under the given path, excluding __pycache__.

    Args:
        path: Root directory to search.

    Returns:
        Sorted list of .py file paths.
    """
    return [
        p
        for p in sorted(path.rglob("*.py"))
        if "__pycache__" not in str(p)
        and p.name not in _EXCLUDED_MODULES
    ]


def _has_docstring(node: ast.AST) -> bool:
    """Return True if the AST node has a non-empty docstring.

    Args:
        node: An ast.FunctionDef, ast.AsyncFunctionDef, or ast.ClassDef.

    Returns:
        True when the first statement in the body is a non-empty string constant.
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    body = node.body  # type: ignore[union-attr]
    if not body:
        return False
    first = body[0]
    return (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
        and bool(first.value.value.strip())
    )


def _is_public(name: str) -> bool:
    """Return True if the name is a public identifier (no leading underscore).

    Args:
        name: Identifier name string.

    Returns:
        True when name does not start with '_'.
    """
    return not name.startswith("_")


@pytest.mark.quality
class TestDocumentationCoverage:
    """All public classes and methods must have docstrings."""

    def test_all_public_classes_have_docstrings(self) -> None:
        """Every public class in src must have a docstring."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef) and _is_public(node.name):
                    if not _has_docstring(node):
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— class '{node.name}' missing docstring"
                        )
        assert not violations, (
            "Missing docstrings on public classes:\n" + "\n".join(violations)
        )

    def test_all_public_methods_have_docstrings(self) -> None:
        """Every public method and function in src must have a docstring."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if _is_public(node.name) and not _has_docstring(node):
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— function/method '{node.name}' missing docstring"
                        )
        assert not violations, (
            "Missing docstrings on public functions/methods:\n" + "\n".join(violations)
        )

    def test_no_empty_docstrings(self) -> None:
        """Docstrings must contain meaningful content (at least 10 characters)."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    body = getattr(node, "body", [])
                    if body and isinstance(body[0], ast.Expr):
                        first_expr = body[0].value
                        if isinstance(first_expr, ast.Constant) and isinstance(
                            first_expr.value, str
                        ):
                            if len(first_expr.value.strip()) < 10:
                                violations.append(
                                    f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                                    f"— '{node.name}' has a too-short docstring"
                                )
        assert not violations, (
            "Trivially short docstrings:\n" + "\n".join(violations)
        )
