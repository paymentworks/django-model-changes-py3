#!/usr/bin/env python3
"""
Script to extract version from setup.py file.
"""

import re
import sys


def extract_version_from_setup_py(file_path="setup.py"):
    """Extract version from setup.py file."""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Supports SemVer, stolen from: https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
        pattern = (
            r'version\s*=\s*[\'"](?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>'
            r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+"
            r'(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?[\'"]'
        )
        match = re.search(pattern, content)

        if match:
            return match.group(1)
        else:
            return "0.0.0"

    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return "0.0.0"


if __name__ == "__main__":
    version = extract_version_from_setup_py()
    print(version)
