"""authentik admin tasks"""

import orjson
from django.utils.translation import gettext_lazy as _
from requests import RequestException
from structlog.stdlib import get_logger

from authentik.analytics.utils import get_analytics_data
from authentik.events.models import Event, EventAction
from authentik.events.system_tasks import SystemTask, TaskStatus, prefill_task
from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP
from authentik.tenants.models import Tenant

LOGGER = get_logger()


@CELERY_APP.task(bind=True, base=SystemTask)
@prefill_task
def send_analytics(self: SystemTask):
    """Send analytics"""
    for tenant in Tenant.objects.filter(ready=True):
        data = get_analytics_data(current_tenant=tenant)
        if not tenant.analytics_enabled or not data:
            self.set_status(TaskStatus.WARNING, "Analytics disabled. Nothing was sent.")
            return
        try:
            response = get_http_session().post(
                "https://customers.goauthentik.io/api/analytics/post/", json=data
            )
            response.raise_for_status()
            self.set_status(
                TaskStatus.SUCCESSFUL,
                "Successfully sent analytics",
                orjson.dumps(
                    data, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS | orjson.OPT_UTC_Z
                ).decode(),
            )
            Event.new(
                EventAction.ANALYTICS_SENT,
                message=_("Analytics sent"),
                analytics_data=data,
            ).save()
        except (RequestException, IndexError) as exc:
            self.set_error(exc)
