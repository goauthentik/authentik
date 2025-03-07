"""authentik Blueprints app"""

from collections.abc import Callable
from importlib import import_module
from inspect import ismethod
from typing import Iterable

from django.apps import AppConfig
from django.db import DatabaseError, InternalError, ProgrammingError
from structlog.stdlib import BoundLogger, get_logger

from authentik.root.signals import startup


class ManagedAppConfig(AppConfig):
    """Basic reconciliation logic for apps"""

    logger: BoundLogger

    RECONCILE_GLOBAL_CATEGORY: str = "global"
    RECONCILE_TENANT_CATEGORY: str = "tenant"

    startup_tasks_default_tenant: Iterable[str] = []
    startup_tasks_all_tenants: Iterable[str] = []

    def __init__(self, app_name: str, *args, **kwargs) -> None:
        super().__init__(app_name, *args, **kwargs)
        self.logger = get_logger().bind(app_name=app_name)

    def ready(self) -> None:
        self.import_related()
        startup.connect(self._on_startup_callback, dispatch_uid=self.label)
        return super().ready()

    def _on_startup_callback(self, sender, **_):
        self._reconcile_global()
        self._reconcile_tenant()

    def import_related(self):
        """Automatically import related modules which rely on just being imported
        to register themselves (mainly django signals and celery tasks)"""

        def import_relative(rel_module: str):
            try:
                module_name = f"{self.name}.{rel_module}"
                import_module(module_name)
                self.logger.info("Imported related module", module=module_name)
            except ModuleNotFoundError:
                pass

        import_relative("checks")
        import_relative("tasks")
        import_relative("signals")

    def import_module(self, path: str):
        """Load module"""
        import_module(path)

    def _reconcile(self, prefix: str) -> None:
        for meth_name in dir(self):
            meth = getattr(self, meth_name)
            if not ismethod(meth):
                continue
            category = getattr(meth, "_authentik_managed_reconcile", None)
            if category != prefix:
                continue
            name = meth_name.replace(prefix, "")
            try:
                self.logger.debug("Starting reconciler", name=name)
                meth()
                self.logger.debug("Successfully reconciled", name=name)
            except (DatabaseError, ProgrammingError, InternalError) as exc:
                self.logger.warning("Failed to run reconcile", name=name, exc=exc)

    @staticmethod
    def reconcile_tenant(func: Callable):
        """Mark a function to be called on startup (for each tenant)"""
        func._authentik_managed_reconcile = ManagedAppConfig.RECONCILE_TENANT_CATEGORY
        return func

    @staticmethod
    def reconcile_global(func: Callable):
        """Mark a function to be called on startup (globally)"""
        func._authentik_managed_reconcile = ManagedAppConfig.RECONCILE_GLOBAL_CATEGORY
        return func

    def _reconcile_tenant(self) -> None:
        """reconcile ourselves for tenanted methods"""
        from authentik.tenants.models import Tenant
        from authentik.tasks.tasks import async_task

        try:
            tenants = list(Tenant.objects.filter(ready=True))
        except (DatabaseError, ProgrammingError, InternalError) as exc:
            self.logger.debug("Failed to get tenants to run reconcile", exc=exc)
            return
        for tenant in tenants:
            with tenant:
                self._reconcile(self.RECONCILE_TENANT_CATEGORY)
                for task in self.startup_tasks_all_tenants:
                    async_task(task)

    def _reconcile_global(self) -> None:
        """
        reconcile ourselves for global methods.
        Used for signals, tasks, etc. Database queries should not be made in here.
        """
        from django_tenants.utils import get_public_schema_name, schema_context
        from authentik.tasks.tasks import async_task

        with schema_context(get_public_schema_name()):
            self._reconcile(self.RECONCILE_GLOBAL_CATEGORY)
            for task in self.startup_tasks_default_tenant:
                async_task(task)


class AuthentikBlueprintsConfig(ManagedAppConfig):
    """authentik Blueprints app"""

    name = "authentik.blueprints"
    label = "authentik_blueprints"
    verbose_name = "authentik Blueprints"
    default = True

    startup_tasks_all_tenants = (
        "authentik.blueprints.v1.tasks.blueprints_discovery",
        "authentik.blueprints.v1.tasks.clear_failed_blueprints",
    )

    @ManagedAppConfig.reconcile_global
    def load_blueprints_v1_tasks(self):
        """Load v1 tasks"""
        self.import_module("authentik.blueprints.v1.tasks")

    def import_models(self):
        super().import_models()
        self.import_module("authentik.blueprints.v1.meta.apply_blueprint")
