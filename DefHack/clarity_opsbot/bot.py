"""Backward-compatible entry point that exposes the modular bot application."""

from .app import build_app, main

__all__ = ["build_app", "main"]


if __name__ == "__main__":  # pragma: no cover
    main()
