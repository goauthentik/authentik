"""Blueprint helpers"""
from functools import wraps
from typing import Callable

from django.apps import apps

from authentik.blueprints.manager import ManagedAppConfig


def apply_blueprint(*files: str):
    """Apply blueprint before test"""

    from authentik.blueprints.v1.importer import Importer

    def wrapper_outer(func: Callable):
        """Apply blueprint before test"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            for file in files:
                with open(file, "r+", encoding="utf-8") as _file:
                    Importer(_file.read()).apply()
            return func(*args, **kwargs)

        return wrapper

    return wrapper_outer


def reconcile_app(app_name: str):
    """Re-reconcile AppConfig methods"""

    def wrapper_outer(func: Callable):
        """Re-reconcile AppConfig methods"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            config = apps.get_app_config(app_name)
            if isinstance(config, ManagedAppConfig):
                config.reconcile()
            return func(*args, **kwargs)

        return wrapper

    return wrapper_outer
