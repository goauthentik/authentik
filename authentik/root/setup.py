import os
import warnings

from cryptography.hazmat.backends.openssl.backend import backend
from defusedxml import defuse_stdlib
from xmlsec import base64_default_line_size

from authentik.lib.config import CONFIG


def setup():
    warnings.filterwarnings("ignore", "SelectableGroups dict interface")
    warnings.filterwarnings(
        "ignore",
        "defusedxml.lxml is no longer supported and will be removed in a future release.",
    )
    warnings.filterwarnings(
        "ignore",
        "defusedxml.cElementTree is deprecated, import from defusedxml.ElementTree instead.",
    )

    defuse_stdlib()
    base64_default_line_size(size=8192)

    if CONFIG.get_bool("compliance.fips.enabled", False):
        backend._enable_fips()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
