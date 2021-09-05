"""Plex tasks"""
from requests import RequestException

from authentik.events.models import Event, EventAction
from authentik.events.monitored_tasks import MonitoredTask, TaskResult, TaskResultStatus
from authentik.root.celery import CELERY_APP
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth


@CELERY_APP.task()
def check_plex_token_all():
    """Check plex token for all plex sources"""
    for source in PlexSource.objects.all():
        check_plex_token.delay(source.slug)


@CELERY_APP.task(bind=True, base=MonitoredTask)
def check_plex_token(self: MonitoredTask, source_slug: int):
    """Check the validity of a Plex source."""
    sources = PlexSource.objects.filter(slug=source_slug)
    if not sources.exists():
        return
    source: PlexSource = sources.first()
    self.set_uid(source.slug)
    auth = PlexAuth(source, source.plex_token)
    try:
        auth.get_user_info()
        self.set_status(TaskResult(TaskResultStatus.SUCCESSFUL, ["Plex token is valid."]))
    except RequestException as exc:
        self.set_status(
            TaskResult(
                TaskResultStatus.ERROR,
                ["Plex token is invalid/an error occurred:", str(exc)],
            )
        )
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=f"Plex token invalid, please re-authenticate source.\n{str(exc)}",
            source=source,
        ).save()
