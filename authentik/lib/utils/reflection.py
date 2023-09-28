"""authentik lib reflection utilities"""
import os
from importlib import import_module
from pathlib import Path

from django.conf import settings
from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME

from authentik.lib.config import CONFIG


def all_subclasses(cls, sort=True):
    """Recursively return all subclassess of cls"""
    classes = set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c, sort=sort)]
    )
    # Check if we're in debug mode, if not exclude classes which have `__debug_only__`
    if not settings.DEBUG:
        # Filter class out when __debug_only__ is not False
        classes = [x for x in classes if not getattr(x, "__debug_only__", False)]
        # classes = filter(lambda x: not getattr(x, "__debug_only__", False), classes)
    if sort:
        return sorted(classes, key=lambda x: x.__name__)
    return classes


def class_to_path(cls: type) -> str:
    """Turn Class (Class or instance) into module path"""
    return f"{cls.__module__}.{cls.__name__}"


def path_to_class(path: str = "") -> type:
    """Import module and return class"""
    parts = path.split(".")
    package = ".".join(parts[:-1])
    _class = getattr(import_module(package), parts[-1])
    return _class


def get_apps():
    """Get list of all authentik apps"""
    from django.apps.registry import apps

    for _app in apps.get_app_configs():
        if _app.name.startswith("authentik"):
            yield _app


def get_env() -> str:
    """Get environment in which authentik is currently running"""
    if "CI" in os.environ:
        return "ci"
    if CONFIG.get_bool("debug"):
        return "dev"
    if SERVICE_HOST_ENV_NAME in os.environ:
        return "kubernetes"
    if Path("/tmp/authentik-mode").exists():  # nosec
        return "compose"
    if "AK_APPLIANCE" in os.environ:
        return os.environ["AK_APPLIANCE"]
    return "custom"
