#!/usr/bin/env python3
"""
Script to extract version from setup.py file.
This avoids regex escaping issues in GitHub Actions.
"""

import re
import sys

def extract_version_from_setup_py(file_path='setup.py'):
    """Extract version from setup.py file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for version= with single or double quotes, supporting semver format
        # This pattern handles: 1.2.3, 1.2.3-alpha.1, 1.2.3+build.123
        pattern = r'version\s*=\s*[\'"]([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?)[\'"]'
        match = re.search(pattern, content)
        
        if match:
            return match.group(1)
        else:
            return '0.0.0'
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return '0.0.0'

if __name__ == '__main__':
    version = extract_version_from_setup_py()
    print(version)
