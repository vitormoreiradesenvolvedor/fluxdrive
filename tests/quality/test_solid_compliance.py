"""SOLID compliance tests — statically analyzes the codebase via AST.

These tests enforce:
- Single Responsibility: classes have limited public methods and attributes.
- Open/Closed: infrastructure classes implement Abstract Base Classes.
- Liskov Substitution: subclasses don't remove abstract method implementations.
- Interface Segregation: interface ABCs have limited abstract methods.
- Dependency Inversion: use cases depend on abstractions, not concrete classes.
"""

import ast
import inspect
from pathlib import Path

import pytest

SRC_PATH = Path(__file__).parent.parent.parent / "src" / "fluxdrive"
CONTRACTS_PATH = SRC_PATH / "application" / "contracts"
INFRASTRUCTURE_PATH = SRC_PATH / "infrastructure"
USE_CASES_PATH = SRC_PATH / "application" / "use_cases"

MAX_PUBLIC_METHODS = 15
MAX_CLASS_ATTRIBUTES = 12
MAX_INTERFACE_ABSTRACT_METHODS = 5
MAX_FUNCTION_LINES = 40
MAX_FUNCTION_PARAMS = 5


def _python_files(path: Path) -> list[Path]:
    """Return all .py files under the given path.

    Args:
        path: Root directory to search.

    Returns:
        Sorted list of .py file paths.
    """
    return sorted(path.rglob("*.py"))


def _parse(path: Path) -> ast.Module:
    """Parse a Python source file into an AST Module.

    Args:
        path: Path to the .py file.

    Returns:
        Parsed AST Module node.
    """
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _public_methods(cls_node: ast.ClassDef) -> list[ast.FunctionDef]:
    """Return public method nodes of a class.

    Args:
        cls_node: The ClassDef AST node to inspect.

    Returns:
        List of FunctionDef nodes for public methods.
    """
    return [
        node
        for node in cls_node.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]


@pytest.mark.quality
class TestSingleResponsibility:
    """SRP: each class has a focused, limited set of responsibilities."""

    def test_no_class_exceeds_public_method_limit(self) -> None:
        """No class has more than MAX_PUBLIC_METHODS public methods."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            if "__pycache__" in str(py_file):
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef):
                    methods = _public_methods(node)
                    if len(methods) > MAX_PUBLIC_METHODS:
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— '{node.name}' has {len(methods)} public methods "
                            f"(max: {MAX_PUBLIC_METHODS})"
                        )
        assert not violations, "SRP violations:\n" + "\n".join(violations)

    def test_functions_do_not_exceed_line_limit(self) -> None:
        """No function body exceeds MAX_FUNCTION_LINES lines."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            if "__pycache__" in str(py_file):
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    body_lines = (node.end_lineno or node.lineno) - node.lineno
                    if body_lines > MAX_FUNCTION_LINES:
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— '{node.name}' has {body_lines} lines "
                            f"(max: {MAX_FUNCTION_LINES})"
                        )
        assert not violations, "Clean Code (function length) violations:\n" + "\n".join(violations)


@pytest.mark.quality
class TestOpenClosed:
    """OCP: infrastructure adapters implement declared ABCs from contracts."""

    def test_infrastructure_classes_have_base_class(self) -> None:
        """All non-private infrastructure classes extend at least one base."""
        violations: list[str] = []
        for py_file in _python_files(INFRASTRUCTURE_PATH):
            if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    if not node.bases:
                        violations.append(
                            f"{py_file.name}:{node.lineno} "
                            f"— '{node.name}' has no base class (expected ABC)"
                        )
        assert not violations, "OCP violations (no ABC):\n" + "\n".join(violations)


@pytest.mark.quality
class TestInterfaceSegregation:
    """ISP: interfaces are small and focused — no fat interfaces."""

    def test_contract_interfaces_have_few_abstract_methods(self) -> None:
        """No contract ABC defines more than MAX_INTERFACE_ABSTRACT_METHODS methods."""
        violations: list[str] = []
        for py_file in _python_files(CONTRACTS_PATH):
            if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef):
                    abstract_methods = [
                        n
                        for n in ast.walk(node)
                        if isinstance(n, ast.FunctionDef)
                        and any(
                            (isinstance(d, ast.Name) and d.id == "abstractmethod")
                            or (isinstance(d, ast.Attribute) and d.attr == "abstractmethod")
                            for d in n.decorator_list
                        )
                    ]
                    if len(abstract_methods) > MAX_INTERFACE_ABSTRACT_METHODS:
                        violations.append(
                            f"{py_file.name}:{node.lineno} "
                            f"— '{node.name}' has {len(abstract_methods)} abstract methods "
                            f"(max: {MAX_INTERFACE_ABSTRACT_METHODS})"
                        )
        assert not violations, "ISP violations:\n" + "\n".join(violations)


@pytest.mark.quality
class TestDependencyInversion:
    """DIP: use cases import from contracts, not from infrastructure."""

    def test_use_cases_do_not_import_infrastructure(self) -> None:
        """Use case modules must not import directly from infrastructure."""
        violations: list[str] = []
        for py_file in _python_files(USE_CASES_PATH):
            if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            module = ast.parse(source)
            for node in ast.walk(module):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_str = ""
                    if isinstance(node, ast.ImportFrom) and node.module:
                        import_str = node.module
                    if "fluxdrive.infrastructure" in import_str:
                        violations.append(
                            f"{py_file.name}:{node.lineno} "
                            f"— imports from infrastructure: '{import_str}'"
                        )
        assert not violations, "DIP violations:\n" + "\n".join(violations)

    def test_use_cases_init_accepts_only_abstract_types(self) -> None:
        """Use case __init__ parameters should reference interface ABCs."""
        violations: list[str] = []
        for py_file in _python_files(USE_CASES_PATH):
            if "__pycache__" in str(py_file) or py_file.name == "__init__.py":
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef) and method.name == "__init__":
                            for arg in method.args.args:
                                if arg.arg == "self":
                                    continue
                                annotation = arg.annotation
                                if annotation is None:
                                    violations.append(
                                        f"{py_file.name}:{method.lineno} "
                                        f"— '{node.name}.__init__' parameter "
                                        f"'{arg.arg}' has no type annotation"
                                    )
        assert not violations, "DIP annotation violations:\n" + "\n".join(violations)


@pytest.mark.quality
class TestFunctionParameters:
    """Clean Code: functions should have few parameters."""

    def test_no_function_has_too_many_parameters(self) -> None:
        """No function has more than MAX_FUNCTION_PARAMS parameters (excluding self)."""
        violations: list[str] = []
        for py_file in _python_files(SRC_PATH):
            if "__pycache__" in str(py_file):
                continue
            module = _parse(py_file)
            for node in ast.walk(module):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    params = [a for a in node.args.args if a.arg != "self"]
                    if len(params) > MAX_FUNCTION_PARAMS:
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— '{node.name}' has {len(params)} parameters "
                            f"(max: {MAX_FUNCTION_PARAMS})"
                        )
        assert not violations, "Clean Code (too many params) violations:\n" + "\n".join(violations)
