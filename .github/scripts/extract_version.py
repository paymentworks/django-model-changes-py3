#!/usr/bin/env python3
"""
Script to extract version from setup.py file.
"""

import re
import sys


def extract_version_from_setup_py(file_path: str = "setup.py"):
    with open(file_path, "r") as f:
        content = f.read()
    # Capture the version string between quotes
    pattern = r'version\s*=\s*[\'"]([^"\']+)[\'"]'
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"Could not find version in {file_path}")
    return match.group(1)


if __name__ == "__main__":
    version = extract_version_from_setup_py()
    print(version)
