"""Endpoint tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.endpoints.connector import EnrollmentMethods
from authentik.endpoints.models import Connector

LOGGER = get_logger()

@actor(description=_("Sync endpoints."))
def endpoints_sync():
    for connector in Connector.objects.filter(enabled=True).order_by("name").select_subclasses():
        LOGGER.info("Syncing connector", connector=connector.name)
        controller = connector.controller
        ctrl = controller(connector)
        if EnrollmentMethods.AUTOMATIC_API not in ctrl.supported_enrollment_methods():
            continue
        ctrl.sync_endpoints()
