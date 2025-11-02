"""Convenience entry point for ``python -m tetrus``."""

from src.tetrus import main as _run_main

__all__ = ["main"]


def main() -> None:
    _run_main()
