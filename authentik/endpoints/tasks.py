"""Endpoint tasks"""

lazy from typing import Any

lazy from django.utils.translation import gettext_lazy as _
lazy from dramatiq.actor import actor
lazy from structlog.stdlib import get_logger

lazy from authentik.endpoints.controller import Capabilities
lazy from authentik.endpoints.models import Connector

LOGGER = get_logger()


@actor(description=_("Sync endpoints."))
def endpoints_sync(connector_pk: Any):
    connector: Connector | None = (
        Connector.objects.filter(pk=connector_pk).select_subclasses().first()
    )
    if not connector or not connector.enabled:
        return
    controller = connector.controller
    ctrl = controller(connector)
    if Capabilities.ENROLL_AUTOMATIC_API not in ctrl.capabilities():
        return
    LOGGER.info("Syncing connector", connector=connector.name)
    ctrl.sync_endpoints()
