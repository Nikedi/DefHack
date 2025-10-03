# Copilot Instructions for DefHack

## Project Overview
DefHack is a Python project organized for modular sensor data processing, with a focus on image analysis and soldier detection. The codebase is structured for extensibility and rapid prototyping, using `uv` for dependency and environment management.

## Architecture & Key Components
- **Main entry points:**
  - `main.py` (root): likely CLI or orchestrator.
  - `DefHack/__main__.py`: package-level entry.
- **Sensors module:**
  - `DefHack/sensors/`: core logic for sensor data, especially images.
  - `images/`: contains image processing pipelines (attribute classification, soldier detection, segmentation).
  - `SensorSchema.py`: defines schemas or interfaces for sensor data.
- **Testing:**
  - `images/tests/`: all image pipeline tests and fixtures.
  - `pytest.ini`: custom pytest config for image tests.

## Developer Workflow
- **Dependency management:**
  - Use `uv` for all Python package operations (install, update, lock).
  - Always update `pyproject.toml` and `uv.lock` when adding/removing dependencies.
- **Testing:**
  - Run tests from the `images/tests/` directory using pytest.
  - Use the uv-managed environment for all test runs.
- **Branching:**
  - Work in feature branches; keep main clean.
- **Documentation:**
  - Update README and relevant doc files for new features.

## Patterns & Conventions
- **Modular design:**
  - Each sensor type (e.g., images) has its own subdirectory and pipeline.
  - Use `__main__.py` for CLI or script entry points in submodules.
- **Schema-first:**
  - Define data schemas/interfaces in dedicated files (e.g., `SensorSchema.py`).
- **Tests:**
  - Place all tests in the relevant `tests/` subdirectory.
  - Use fixtures in `conftests.py` for reusable test setup.

## Integration Points
- **External dependencies:**
  - Managed via `uv` and declared in `pyproject.toml`.
- **Image models:**
  - Model definitions in `images/models.py`.
  - Processing logic in `prosses_image.py`, `classify_attributes.py`, `detect_soldiers.py`, `segment_soldiers.py`.

## Example Commands
- Install dependencies: `uv sync`
- Add package: `uv add <package>`
- Run tests: `pytest DefHack/sensors/images/tests/`

## Key Files & Directories
- `main.py`, `DefHack/__main__.py`: entry points
- `DefHack/sensors/`: sensor logic
- `DefHack/sensors/images/`: image pipelines
- `DefHack/sensors/images/tests/`: tests
- `pyproject.toml`, `uv.lock`: dependency management

---
If any section is unclear or missing, please provide feedback to improve these instructions.
