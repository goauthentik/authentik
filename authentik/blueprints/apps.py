"""authentik Blueprints app"""

import traceback
from collections.abc import Callable
from importlib import import_module

from django.apps import AppConfig
from django.conf import settings
from django.db import DatabaseError, InternalError, ProgrammingError
from dramatiq.broker import get_broker
from structlog.stdlib import BoundLogger, get_logger

from authentik.lib.utils.time import fqdn_rand
from authentik.root.signals import startup
from authentik.tasks.schedules.common import ScheduleSpec


class ManagedAppConfig(AppConfig):
    """Basic reconciliation logic for apps"""

    logger: BoundLogger

    def __init__(self, app_name: str, *args, **kwargs) -> None:
        super().__init__(app_name, *args, **kwargs)
        self.logger = get_logger().bind(app_name=app_name)

    def ready(self) -> None:
        self.import_related()
        startup.connect(self._on_startup_callback, dispatch_uid=self.label)
        return super().ready()

    def _on_startup_callback(self, sender, **_):
        self._reconcile()

    def import_related(self):
        """Automatically import related modules which rely on just being imported
        to register themselves (mainly django signals and tasks)"""

        def import_relative(rel_module: str):
            try:
                module_name = f"{self.name}.{rel_module}"
                import_module(module_name)
                self.logger.info("Imported related module", module=module_name)
            except ModuleNotFoundError as exc:
                if settings.DEBUG:
                    # This is a heuristic for determining whether the exception was caused
                    # "directly" by the `import_module` call or whether the initial import
                    # succeeded and a later import (within the existing module) failed.
                    # 1. <the calling function>
                    # 2. importlib.import_module
                    # 3. importlib._bootstrap._gcd_import
                    # 4. importlib._bootstrap._find_and_load
                    # 5. importlib._bootstrap._find_and_load_unlocked
                    STACK_LENGTH_HEURISTIC = 5

                    stack_length = len(traceback.extract_tb(exc.__traceback__))
                    if stack_length > STACK_LENGTH_HEURISTIC:
                        raise

        import_relative("checks")
        import_relative("tasks")
        import_relative("signals")

    def import_module(self, path: str):
        """Load module"""
        import_module(path)

    def _reconcile(self) -> None:
        for name in dir(self):
            # Check the attribute on the class to avoid evaluating @property descriptors.
            # Using getattr(self, ...) on a @property would evaluate it, which can trigger
            # expensive side effects (e.g. schedule_specs iterating all providers
            # and running PolicyEngine queries for every user).
            class_attr = getattr(type(self), name, None)
            if class_attr is None or isinstance(class_attr, property):
                continue
            if not callable(class_attr):
                continue
            should_call = getattr(class_attr, "_authentik_managed_reconcile", False)
            if not should_call:
                continue
            meth = getattr(self, name)
            try:
                self.logger.debug("Starting reconciler", name=name)
                meth()
                self.logger.debug("Successfully reconciled", name=name)
            except (DatabaseError, ProgrammingError, InternalError) as exc:
                self.logger.warning("Failed to run reconcile", name=name, exc=exc)

    @staticmethod
    def reconcile(func: Callable):
        """Mark a function to be called on startup (for each tenant)"""
        func._authentik_managed_reconcile = True
        return func

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        """Get a list of schedule specs that must exist"""
        return []


class AuthentikBlueprintsConfig(ManagedAppConfig):
    """authentik Blueprints app"""

    name = "authentik.blueprints"
    label = "authentik_blueprints"
    verbose_name = "authentik Blueprints"
    default = True

    def import_models(self):
        super().import_models()
        self.import_module("authentik.blueprints.v1.meta.apply_blueprint")

    @ManagedAppConfig.reconcile
    def tasks_middlewares(self):
        from authentik.blueprints.v1.tasks import BlueprintWatcherMiddleware

        get_broker().add_middleware(BlueprintWatcherMiddleware())

    @property
    def schedule_specs(self) -> list[ScheduleSpec]:
        from authentik.blueprints.v1.tasks import blueprints_discovery, clear_failed_blueprints

        return [
            ScheduleSpec(
                actor=blueprints_discovery,
                crontab=f"{fqdn_rand('blueprints_v1_discover')} * * * *",
                send_on_startup=True,
            ),
            ScheduleSpec(
                actor=clear_failed_blueprints,
                crontab=f"{fqdn_rand('blueprints_v1_cleanup')} * * * *",
                send_on_startup=True,
            ),
        ]
