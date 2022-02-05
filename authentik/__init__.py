"""authentik"""
from os import environ
from typing import Optional

__version__ = "2022.1.4"
ENV_GIT_HASH_KEY = "GIT_BUILD_HASH"


def get_build_hash(fallback: Optional[str] = None) -> str:
    """Get build hash"""
    return environ.get(ENV_GIT_HASH_KEY, fallback if fallback else "")


def get_full_version() -> str:
    """Get full version, with build hash appended"""
    version = __version__
    if (build_hash := get_build_hash()) != "":
        version += "." + build_hash
    return version
