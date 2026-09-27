#!/usr/bin/env python3
"""Compatibility launcher; the installed CLI is src.cli:main."""

from src.cli import main, setup_argument_parser

__all__ = ["main", "setup_argument_parser"]

if __name__ == "__main__":
    raise SystemExit(main())
