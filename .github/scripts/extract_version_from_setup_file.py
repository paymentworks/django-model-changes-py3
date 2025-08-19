#!/usr/bin/env python3
"""
Script to extract version from setup.py file.
"""

import re
import sys


<<<<<<< Updated upstream:.github/scripts/extract_version.py
def extract_version_from_setup_py(file_path: str = "setup.py"):
    with open(file_path, "r") as f:
        content = f.read()
    # Capture the version string between quotes
    pattern = r'version\s*=\s*[\'"]([^"\']+)[\'"]'
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"Could not find version in {file_path}")
    return match.group(1)
=======
def extract_version_from_setup_file(file_path="setup.py"):
    """Extract version from setup.py file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Simple regex to capture the version string between quotes
        pattern = r'version\s*=\s*[\'"]([^"\']+)[\'"]'

        match = re.search(pattern, content)

        if match:
            return match.group(1)
        else:
            return "0.0.0"

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return "0.0.0"
>>>>>>> Stashed changes:.github/scripts/extract_version_from_setup_file.py


if __name__ == "__main__":
    version = extract_version_from_setup_file()
    print(version)
