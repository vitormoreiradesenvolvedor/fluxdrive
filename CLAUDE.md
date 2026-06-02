# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install all dependencies (required before running any tool)
python3 -m pip install -e ".[dev]"

# Run all tests
python3 -m pytest tests/ -q

# Run only unit tests (fast, no Qt needed)
python3 -m pytest tests/unit/ -q

# Run only quality compliance tests (AST-based, no Qt display required)
python3 -m pytest tests/quality/ -p no:qt -q

# Run a single test
python3 -m pytest tests/unit/domain/test_device.py::TestDevice::test_size_gib_returns_correct_value -v

# Run all quality checks locally (same as CI)
python3 -m black --check src/ tests/
python3 -m isort --check-only src/ tests/
python3 -m mypy src/fluxdrive --strict --ignore-missing-imports
python3 -m pylint src/fluxdrive --fail-under=9.5 --rcfile=.pylintrc
python3 -m interrogate src/fluxdrive --fail-under=100
python3 -m pytest tests/ --cov=src/fluxdrive --cov-fail-under=80

# Auto-fix formatting
python3 -m black src/ tests/
python3 -m isort src/ tests/

# Generate local dev AppImage (runs unit tests first)
bash scripts/dev-release.sh

# Set up git hooks after cloning
bash scripts/setup-hooks.sh
```

## Architecture

FluxDrive follows **Clean Architecture** with strict layering. Import direction is always inward: `ui → application → domain`, and `infrastructure → application → domain`. The domain layer never imports from any outer layer.

```
src/fluxdrive/
├── domain/          # No dependencies on any other layer
│   ├── entities/    # Device, IsoImage, WriteConfig — all frozen dataclasses
│   ├── value_objects/  # PartitionScheme, FileSystem, TargetSystem, WriteMode, etc.
│   └── exceptions/  # DeviceError, WriteError hierarchies
├── application/     # Depends only on domain
│   ├── contracts/   # Abstract interfaces (ports) — IDeviceScanner, IIsoWriter, etc.
│   └── use_cases/   # One class per operation; UseCaseRegistry groups them all
├── infrastructure/  # Implements contracts; uses subprocess, pyudev, requests
│   ├── device_scanner_udev.py
│   ├── iso_writer_dd.py / iso_writer_iso.py  # Strategy pattern
│   ├── drive_formatter.py, hash_verifier.py, iso_detector.py, etc.
└── ui/              # PyQt6; depends on application layer via MainViewModel
    ├── main_window.py
    ├── view_models/main_view_model.py  # Owns UseCaseRegistry, emits Qt signals
    └── dialogs/
```

**Composition Root** is `main.py::_compose_view_model()` — the only place that wires concrete infrastructure classes to their abstract interfaces.

**`UseCaseRegistry`** (`application/use_cases/use_case_registry.py`) is a frozen dataclass grouping all 6 use cases. Pass it as a single argument to avoid constructor bloat.

**Strategy pattern** for write operations: `WriteIsoUseCase` holds a list of `IIsoWriter` implementations and calls `can_handle()` to select `IsoModeWriter` or `DdIsoWriter` based on `WriteConfig.write_mode`.

**`MainViewModel`** runs long write operations in `_WriteWorker(QThread)` and communicates back to the UI exclusively via `pyqtSignal`s (`write_progress`, `write_finished`, `write_error`).

## Quality Gate (non-negotiable, enforced on every PR)

All 10 checks must pass. PRs are blocked by GitHub branch protection if any fails.

| Check | Tool | Threshold |
|-------|------|-----------|
| Formatting | `black` + `isort` | zero diff |
| Type safety | `mypy --strict` | zero errors |
| Linting + SOLID | `pylint` | ≥ 9.5/10 |
| Docstrings | `interrogate` | 100% public API |
| Complexity | `radon cc` | CC ≤ B (≤ 10) |
| Security | `bandit` | no HIGH severity |
| Tests | `pytest` | 100% pass |
| Coverage | `pytest-cov` | ≥ 80% |
| SOLID compliance | `tests/quality/test_solid_compliance.py` | all pass |
| Design patterns | `tests/quality/test_design_patterns.py` | all pass |

Custom quality rules enforced by AST analysis in `tests/quality/`:
- No public method/function body > 40 lines
- No function with > 5 parameters (excluding `self`)
- No class with > 12 instance attributes
- Use cases must not import from `infrastructure`
- Domain layer must not import from `application`, `infrastructure`, or `ui`

## Git Workflow

```
master ← only from development (via PR)
development ← only from feature/*, fix/*, chore/*, refactor/*, hotfix/*, test/*, docs/*, ci/*, perf/*
```

- **Never commit directly** to `master` or `development` — local hooks block it
- **Never push directly** to `master` or `development` — GitHub rulesets block it
- Branches must be created from `development` (post-checkout hook auto-corrects if created from master)
- Commit messages must follow Conventional Commits: `type(scope): description`
- PRs to `development` must pass all 10 quality checks before merge
- Feature branches are auto-deleted after merge (`delete_branch_on_merge=true`)

## Key constraints

- **Coverage omits**: `*/ui/*`, `*/infrastructure/*`, `*/main.py` — these require OS resources (block devices, Qt display, network). Tests focus on domain + application layers.
- **PyQt6 linting**: `extension-pkg-allow-list=PyQt6` in `.pylintrc` requires system Qt libs to be installed. The CI linting job installs `libegl1` for this reason.
- **SOLID quality tests**: run with `-p no:qt` because they only do AST analysis and don't need a Qt display.
- **Infrastructure tests**: mock all `subprocess` calls; never call real `parted`, `mkfs`, or `dd` in tests.
- Write operations require root. The app warns on startup if not root.
