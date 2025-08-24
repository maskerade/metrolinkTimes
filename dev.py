#!/usr/bin/env python3
"""Development utilities for Metrolink Times"""

import subprocess
import sys
from pathlib import Path


def run_dev():
    """Run the development server with auto-reload"""
    cmd = [
        "uv", "run", "uvicorn",
        "metrolinkTimes.api:app",
        "--host", "0.0.0.0",
        "--port", "5000",
        "--reload",
        "--log-level", "info"
    ]
    subprocess.run(cmd)


def run_tests():
    """Run the test suite"""
    cmd = ["uv", "run", "pytest", "-v"]
    subprocess.run(cmd)


def lint():
    """Run linting with ruff"""
    cmd = ["uv", "run", "ruff", "check", "metrolinkTimes/"]
    subprocess.run(cmd)


def format_code():
    """Format code with ruff"""
    cmd = ["uv", "run", "ruff", "format", "metrolinkTimes/"]
    subprocess.run(cmd)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/dev.py [dev|test|lint|format]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "dev":
        run_dev()
    elif command == "test":
        run_tests()
    elif command == "lint":
        lint()
    elif command == "format":
        format_code()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()