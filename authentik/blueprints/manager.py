"""Managed objects manager"""
from importlib import import_module
from inspect import ismethod

from django.apps import AppConfig
from django.db import DatabaseError, InternalError, ProgrammingError
from structlog.stdlib import get_logger

LOGGER = get_logger()


class ManagedAppConfig(AppConfig):
    """Basic reconciliation logic for apps"""

    def ready(self) -> None:
        self.reconcile()
        return super().ready()

    def import_module(self, path: str):
        """Load module"""
        import_module(path)

    def reconcile(self) -> None:
        """reconcile ourselves"""
        prefix = "reconcile_"
        for meth_name in dir(self):
            meth = getattr(self, meth_name)
            if not ismethod(meth):
                continue
            if not meth_name.startswith(prefix):
                continue
            name = meth_name.replace(prefix, "")
            try:
                meth()
                LOGGER.debug("Successfully reconciled", name=name)
            except (DatabaseError, ProgrammingError, InternalError) as exc:
                LOGGER.debug("Failed to run reconcile", name=name, exc=exc)
