"""passbook lib reflection utilities"""
from importlib import import_module

from django.conf import settings


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


def class_to_path(cls):
    """Turn Class (Class or instance) into module path"""
    return f"{cls.__module__}.{cls.__name__}"


def path_to_class(path):
    """Import module and return class"""
    if not path:
        return None
    parts = path.split(".")
    package = ".".join(parts[:-1])
    _class = getattr(import_module(package), parts[-1])
    return _class


def get_apps():
    """Get list of all passbook apps"""
    from django.apps.registry import apps

    for _app in apps.get_app_configs():
        if _app.name.startswith("passbook"):
            yield _app
