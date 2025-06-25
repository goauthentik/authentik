"""Plex tasks"""

from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from requests import RequestException

from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth
from authentik.tasks.models import Task


@actor(description=_("Check the validity of a Plex source."))
def check_plex_token(source_pk: str):
    """Check the validity of a Plex source."""
    self: Task = CurrentTask.get_task()
    sources = PlexSource.objects.filter(pk=source_pk)
    if not sources.exists():
        return
    source: PlexSource = sources.first()
    auth = PlexAuth(source, source.plex_token)
    try:
        auth.get_user_info()
        self.info("Plex token is valid.")
    except RequestException as exc:
        error = exception_to_string(exc)
        if len(source.plex_token) > 0:
            error = error.replace(source.plex_token, "$PLEX_TOKEN")
        self.error(
            "Plex token is invalid/an error occurred:",
            error,
        )
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=f"Plex token invalid, please re-authenticate source.\n{error}",
            source=source,
        ).save()
