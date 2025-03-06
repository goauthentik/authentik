#!/usr/bin/env python3
"""
Generates a Semantic Versioning identifier, suffixed with a timestamp.
"""

from time import time

from authentik import __version__ as package_version

"""
See: https://semver.org/#spec-item-9 (Pre-release spec)
"""
pre_release_timestamp = int(time())

print(f"{package_version}-{pre_release_timestamp}")
