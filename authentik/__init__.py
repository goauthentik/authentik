"""authentik root module"""
from os import environ
from typing import Optional

__version__ = "2023.8.3"
ENV_GIT_HASH_KEY = "GIT_BUILD_HASH"


def get_build_hash(fallback: Optional[str] = None) -> str:
    """Get build hash"""
    build_hash = environ.get(ENV_GIT_HASH_KEY, fallback if fallback else "")
    return fallback if build_hash == "" and fallback else build_hash


def get_full_version() -> str:
    """Get full version, with build hash appended"""
    version = __version__
    if (build_hash := get_build_hash()) != "":
        version += "." + build_hash
    return version
