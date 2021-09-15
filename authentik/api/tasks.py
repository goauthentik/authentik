"""API tasks"""

from authentik.lib.utils.http import get_http_session
from authentik.root.celery import CELERY_APP

SENTRY_SESSION = get_http_session()


@CELERY_APP.task(bind=True)
def sentry_proxy(payload: str):
    """Relay data to sentry"""
    SENTRY_SESSION.post(
        "https://sentry.beryju.org/api/8/envelope/",
        data=payload,
        headers={
            "Content-Type": "application/octet-stream",
        },
        timeout=10,
    )
