# DefHack project


## Development with uv

This project uses [uv](https://github.com/astral-sh/uv) for Python package management and development workflow. uv is a fast Python package manager and build tool that replaces pip and virtualenv for most tasks.

### Getting Started

1. **Install uv** (if you don't have it):
	```pwsh
	pip install uv
	```

2. **Install dependencies:**
	```pwsh
	uv pip install -r requirements.txt
	```
	Or, if using `pyproject.toml`:
	```pwsh
	uv pip install -r pyproject.toml
	```

3. **Add a new dependency:**
	```pwsh
	uv pip install <package>
	```
	This will update your lockfile automatically.

4. **Update dependencies:**
	```pwsh
	uv pip update
	```

### Development Workflow

- Make all changes in a feature branch.
- Use `uv` to manage dependencies and environments.
- Run your code and tests using the uv-managed environment.
- Keep `pyproject.toml` and `uv.lock` up to date.
- Before pushing, ensure all dependencies are locked and documented.

For more details, see the [uv documentation](https://github.com/astral-sh/uv).

## Configuring sensor backends

The sensor pipeline ships with lightweight heuristics by default so it works
out-of-the-box.  To enable stronger models such as TinyYOLO (detection) or
FastSeg (segmentation), edit `DefHack/sensors/settings.py` and change the
`detection_backend` and `segmentation_backend` values.  Remember to install the
corresponding dependencies before switching backends.


