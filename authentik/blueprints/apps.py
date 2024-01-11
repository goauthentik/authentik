"""authentik Blueprints app"""

from importlib import import_module
from inspect import ismethod

from django.apps import AppConfig
from django.db import DatabaseError, InternalError, ProgrammingError
from structlog.stdlib import BoundLogger, get_logger


class ManagedAppConfig(AppConfig):
    """Basic reconciliation logic for apps"""

    _logger: BoundLogger

    RECONCILE_PREFIX: str = "reconcile_"
    RECONCILE_TENANT_PREFIX: str = "reconcile_tenant_"

    def __init__(self, app_name: str, *args, **kwargs) -> None:
        super().__init__(app_name, *args, **kwargs)
        self._logger = get_logger().bind(app_name=app_name)

    def ready(self) -> None:
        self.reconcile()
        self.reconcile_tenant()
        return super().ready()

    def import_module(self, path: str):
        """Load module"""
        import_module(path)

    def _reconcile(self, prefix: str) -> None:
        for meth_name in dir(self):
            meth = getattr(self, meth_name)
            if not ismethod(meth):
                continue
            if not meth_name.startswith(prefix):
                continue
            name = meth_name.replace(prefix, "")
            try:
                self._logger.debug("Starting reconciler", name=name)
                meth()
                self._logger.debug("Successfully reconciled", name=name)
            except (DatabaseError, ProgrammingError, InternalError) as exc:
                self._logger.warning("Failed to run reconcile", name=name, exc=exc)

    def reconcile_tenant(self) -> None:
        """reconcile ourselves for tenanted methods"""
        from authentik.tenants.models import Tenant

        try:
            tenants = list(Tenant.objects.filter(ready=True))
        except (DatabaseError, ProgrammingError, InternalError) as exc:
            self._logger.debug("Failed to get tenants to run reconcile", exc=exc)
            return
        for tenant in tenants:
            with tenant:
                self._reconcile(self.RECONCILE_TENANT_PREFIX)

    def reconcile(self) -> None:
        """reconcile ourselves"""
        from django_tenants.utils import get_public_schema_name, schema_context

        # Special case for the authentik_tenants app, as we need to create the default tenant
        # before being able to use it
        if self.label == "authentik_tenants":
            with schema_context(get_public_schema_name()):
                self._reconcile(self.RECONCILE_PREFIX)
            return

        from authentik.tenants.models import Tenant

        try:
            default_tenant = Tenant.objects.get(schema_name=get_public_schema_name())
        except (DatabaseError, ProgrammingError, InternalError) as exc:
            self._logger.debug("Failed to get default tenant to run reconcile", exc=exc)
            return
        with default_tenant:
            self._reconcile(self.RECONCILE_PREFIX)


class AuthentikBlueprintsConfig(ManagedAppConfig):
    """authentik Blueprints app"""

    name = "authentik.blueprints"
    label = "authentik_blueprints"
    verbose_name = "authentik Blueprints"
    default = True

    def reconcile_load_blueprints_v1_tasks(self):
        """Load v1 tasks"""
        self.import_module("authentik.blueprints.v1.tasks")

    def reconcile_tenant_blueprints_discovery(self):
        """Run blueprint discovery"""
        from authentik.blueprints.v1.tasks import blueprints_discovery, clear_failed_blueprints

        blueprints_discovery.delay()
        clear_failed_blueprints.delay()

    def import_models(self):
        super().import_models()
        self.import_module("authentik.blueprints.v1.meta.apply_blueprint")
