"""authentik root module"""

from functools import lru_cache
from os import environ

VERSION = "2025.12.0"
ENV_GIT_HASH_KEY = "GIT_BUILD_HASH"


@lru_cache
def authentik_version() -> str:
    return VERSION


@lru_cache
def authentik_build_hash(fallback: str | None = None) -> str:
    """Get build hash"""
    build_hash = environ.get(ENV_GIT_HASH_KEY, fallback if fallback else "")
    return fallback if build_hash == "" and fallback else build_hash


@lru_cache
def authentik_full_version() -> str:
    """Get full version, with build hash appended"""
    version = authentik_version()
    if (build_hash := authentik_build_hash()) != "":
        return f"{version}+{build_hash}"
    return version
