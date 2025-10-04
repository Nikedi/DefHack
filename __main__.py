import importlib
import sys

def _invoke_callable(obj):
    if callable(obj):
        return obj()
    return None

def main():
    pkg_name = __package__ or (__name__.split(".", 1)[0] if "." in __name__ else __name__)
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception as e:
        raise SystemExit(f"Failed to import package '{pkg_name}': {e}")

    # prefer package-level entrypoints
    for attr in ("main", "run"):
        obj = getattr(pkg, attr, None)
        if callable(obj):
            return _invoke_callable(obj)

    # fallback to common submodules
    for modname in ("cli", "main"):
        try:
            mod = importlib.import_module(f"{pkg_name}.{modname}")
        except Exception:
            continue
        for attr in ("main", "run"):
            obj = getattr(mod, attr, None)
            if callable(obj):
                return _invoke_callable(obj)

    raise SystemExit(
        "No entry point found. Provide a callable 'main' or 'run' in the package or in a 'cli'/'main' submodule."
    )

if __name__ == "__main__":
    sys.exit(main())
