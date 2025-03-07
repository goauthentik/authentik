"""Plex tasks"""

from requests import RequestException

from authentik.events.models import Event, EventAction, TaskStatus
from authentik.lib.utils.errors import exception_to_string
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth
from authentik.tasks.tasks import TaskData, task


@task()
def check_plex_token_all():
    """Check plex token for all plex sources"""
    for source in PlexSource.objects.all():
        check_plex_token.delay(source.slug)


@task(bind=True)
def check_plex_token(self: TaskData, source_slug: int):
    """Check the validity of a Plex source."""
    sources = PlexSource.objects.filter(slug=source_slug)
    if not sources.exists():
        return
    source: PlexSource = sources.first()
    self.set_uid(source.slug)
    auth = PlexAuth(source, source.plex_token)
    try:
        auth.get_user_info()
        self.set_status(TaskStatus.SUCCESSFUL, "Plex token is valid.")
    except RequestException as exc:
        error = exception_to_string(exc)
        if len(source.plex_token) > 0:
            error = error.replace(source.plex_token, "$PLEX_TOKEN")
        self.set_status(
            TaskStatus.ERROR,
            "Plex token is invalid/an error occurred:",
            error,
        )
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=f"Plex token invalid, please re-authenticate source.\n{error}",
            source=source,
        ).save()
