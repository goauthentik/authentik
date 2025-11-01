"""Blueprint helpers"""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from django.apps import apps

from authentik.blueprints.apps import ManagedAppConfig
from authentik.blueprints.models import BlueprintInstance

P = ParamSpec("P")
R = TypeVar("R")


def apply_blueprint(*files: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Apply blueprint before test"""

    from authentik.blueprints.v1.importer import Importer

    def wrapper_outer(func: Callable[P, R]) -> Callable[P, R]:
        """Apply blueprint before test"""

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for file in files:
                content = BlueprintInstance(path=file).retrieve()
                Importer.from_string(content).apply()
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
                config._on_startup_callback(None)
            return func(*args, **kwargs)

        return wrapper

    return wrapper_outer
