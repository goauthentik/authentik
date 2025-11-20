"""Endpoint tasks"""

from typing import Any

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.endpoints.controller import EnrollmentMethods
from authentik.endpoints.models import Connector

LOGGER = get_logger()


@actor(description=_("Sync endpoints."))
def endpoints_sync(connector_pk: Any):
    connector: Connector | None = (
        Connector.objects.filter(pk=connector_pk).select_subclasses().first()
    )
    if not connector:
        return
    controller = connector.controller
    ctrl = controller(connector)
    if EnrollmentMethods.AUTOMATIC_API not in ctrl.supported_enrollment_methods():
        return
    LOGGER.info("Syncing connector", connector=connector.name)
    ctrl.sync_endpoints()
