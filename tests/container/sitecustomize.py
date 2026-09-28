"""Loaded through PYTHONPATH when scripts/test_docker.sh runs the suite in the server image.

The distroless image stays unchanged: this file, the dev-only packages and the KDC tools
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

# Check that nobody mounted a shell, because code that runs one would pass the tests and still
# fail in an image without one. A mount is the only way to add a shell to an unchanged image
if os.path.ismount("/bin/sh"):
    _refuse("a shell is mounted in")

# Make the dev-only packages that the tests need importable. They go after the image's own
# packages, so that a package the image ships always comes from the image
site.addsitedir("/test-kit/devdeps")

# Put the kit's KDC tools on PATH, because the Kerberos tests start a KDC through k5test, which
# looks for the tools there, and the image doesn't ship them
os.environ["PATH"] = f"/test-kit/krb5/bin:{os.environ['PATH']}"

# Point k5test at the kit's KDC database module, because its own search runs krb5-config through
# a shell and only looks in the image, which has neither the module nor krb5-config
import k5test._utils  # noqa: E402

k5test._utils._PLUGIN_DIR = "/test-kit/krb5/plugins"
