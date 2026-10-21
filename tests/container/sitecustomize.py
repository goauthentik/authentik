"""Loaded through PYTHONPATH when scripts/test_docker.sh runs the suite in the server image.

The server image stays unchanged: this file, the dev-only packages and the KDC tools
for the Kerberos tests are mounted at /test-kit.

Nothing mounted may stand in for something the image lacks, so refuse to start when that
could happen.
"""

import os
import site
import sys
from typing import NoReturn


def _refuse(problem: str) -> NoReturn:
    sys.stderr.write(f"test kit: {problem}, so the tests would not test the real image\n")
    # Exit without raising, because site.py turns an exception into a warning and continues
    os._exit(3)


# Check that LD_LIBRARY_PATH isn't set, because it could make the image load a library it doesn't
# ship from the kit, and the tests would pass on an image that fails in production
if "LD_LIBRARY_PATH" in os.environ:
    _refuse("LD_LIBRARY_PATH is set")

# Make the dev-only packages that the tests need importable. They go after the image's own
# packages, so that a package the image ships always comes from the image
site.addsitedir("/test-kit/devdeps")

# Point k5test at the kit's KDC tools, because the Kerberos tests start a KDC through it and the
# image doesn't ship them. They stay off PATH, so code under test can't run them either
import k5test.realm  # noqa: E402

k5test.realm._discover_path = lambda name, default, paths: f"/test-kit/krb5/bin/{name}"

# Point k5test at the kit's KDC database module, because its own search runs krb5-config through
# a shell and only looks in the image, which has neither the module nor krb5-config
import k5test._utils  # noqa: E402

k5test._utils._PLUGIN_DIR = "/test-kit/krb5/plugins"
