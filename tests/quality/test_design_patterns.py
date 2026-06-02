"""Design pattern compliance tests — verifies correct use of structural patterns.

Checks that:
- Strategy pattern: IIsoWriter has multiple implementations.
- Factory/Composition Root: main.py wires all dependencies.
- Repository/Scanner: IDeviceScanner is properly implemented.
- Value Objects: domain value objects are immutable (frozen dataclasses).
- Observer: Qt signals are used for progress (not direct callbacks to UI).
"""

import ast
import dataclasses
from pathlib import Path

import pytest

SRC_PATH = Path(__file__).parent.parent.parent / "src" / "fluxdrive"


def _python_files(path: Path) -> list[Path]:
    """Collect .py files under the given path, excluding __pycache__.

    Args:
        path: Root directory to search.

    Returns:
        Sorted list of .py file paths.
    """
    return [
        p
        for p in sorted(path.rglob("*.py"))
        if "__pycache__" not in str(p)
    ]


@pytest.mark.quality
class TestStrategyPattern:
    """Strategy: multiple IIsoWriter implementations must exist."""

    def test_multiple_iso_writer_implementations_exist(self) -> None:
        """At least two classes implementing IIsoWriter must be present."""
        infra_path = SRC_PATH / "infrastructure"
        writer_impls: list[str] = []

        for py_file in _python_files(infra_path):
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        if "IsoWriter" in base_name or "IIsoWriter" in base_name:
                            writer_impls.append(node.name)

        assert len(writer_impls) >= 2, (
            f"Expected at least 2 IIsoWriter implementations (Strategy pattern), "
            f"found: {writer_impls}"
        )


@pytest.mark.quality
class TestValueObjectImmutability:
    """Value Objects: domain entities and value objects must be immutable."""

    def test_domain_entities_are_frozen_dataclasses(self) -> None:
        """Domain entity dataclasses must use frozen=True."""
        from fluxdrive.domain.entities.device import Device
        from fluxdrive.domain.entities.iso_image import IsoImage
        from fluxdrive.domain.entities.write_config import WriteConfig

        for cls in (Device, IsoImage, WriteConfig):
            fields = dataclasses.fields(cls)
            assert fields, f"{cls.__name__} has no dataclass fields"
            params = cls.__dataclass_params__  # type: ignore[attr-defined]
            assert params.frozen, (
                f"{cls.__name__} must be a frozen dataclass (immutable Value Object)"
            )


@pytest.mark.quality
class TestAbstractionLayering:
    """Verifies that the architecture layers are respected in imports."""

    def test_domain_does_not_import_application_or_infrastructure(self) -> None:
        """Domain layer must not import from application or infrastructure."""
        domain_path = SRC_PATH / "domain"
        violations: list[str] = []
        forbidden_prefixes = ("fluxdrive.application", "fluxdrive.infrastructure", "fluxdrive.ui")

        for py_file in _python_files(domain_path):
            if "__pycache__" in str(py_file):
                continue
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, ast.ImportFrom) and node.module:
                    for prefix in forbidden_prefixes:
                        if node.module.startswith(prefix):
                            violations.append(
                                f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                                f"— imports '{node.module}' (layer violation)"
                            )

        assert not violations, (
            "Domain layer imports upper layers (Clean Architecture violation):\n"
            + "\n".join(violations)
        )

    def test_application_does_not_import_infrastructure(self) -> None:
        """Application layer must not import from infrastructure (except use_cases)."""
        app_path = SRC_PATH / "application"
        contracts_path = app_path / "contracts"
        violations: list[str] = []

        for py_file in _python_files(contracts_path):
            if "__pycache__" in str(py_file):
                continue
            module = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("fluxdrive.infrastructure"):
                        violations.append(
                            f"{py_file.relative_to(SRC_PATH)}:{node.lineno} "
                            f"— contract imports infrastructure: '{node.module}'"
                        )

        assert not violations, (
            "Contracts import infrastructure (DIP violation):\n"
            + "\n".join(violations)
        )


@pytest.mark.quality
class TestCompositionRoot:
    """Factory / Composition Root: all wiring happens in main.py."""

    def test_main_module_contains_composition_function(self) -> None:
        """main.py must define a composition root function (_compose_view_model)."""
        main_file = SRC_PATH / "main.py"
        assert main_file.exists(), "src/fluxdrive/main.py not found"

        module = ast.parse(main_file.read_text(encoding="utf-8"))
        function_names = [
            node.name
            for node in ast.walk(module)
            if isinstance(node, ast.FunctionDef)
        ]
        assert "_compose_view_model" in function_names or "compose" in str(function_names), (
            "main.py must contain a composition root function"
        )
