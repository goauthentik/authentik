import os
import warnings

from cryptography.hazmat.backends.openssl.backend import backend
from defusedxml import defuse_stdlib

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

    if CONFIG.get_bool("compliance.fips.enabled", False):
        backend._enable_fips()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
