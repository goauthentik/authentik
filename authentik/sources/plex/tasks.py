"""Plex tasks"""

from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from requests import RequestException

from authentik.events.models import Event, EventAction
from authentik.lib.utils.errors import exception_to_string
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth
from authentik.tasks.middleware import CurrentTask


@actor(description=_("Check the validity of a Plex source."))
def check_plex_token(source_pk: str):
    """Check the validity of a Plex source."""
    self = CurrentTask.get_task()
    sources = PlexSource.objects.filter(pk=source_pk)
    if not sources.exists():
        return
    source: PlexSource = sources.first()
    plex_token = source.secret.value if source.secret else ""
    try:
        if not plex_token:
            raise RequestException("No Plex token configured")
        PlexAuth(source, plex_token).get_user_info()
        self.info("Plex token is valid.")
    except RequestException as exc:
        error = exception_to_string(exc)
        if plex_token:
            error = error.replace(plex_token, "$PLEX_TOKEN")
        self.error("Plex token is invalid/an error occurred")
        self.error(error)
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            message=f"Plex token invalid, please re-authenticate source.\n{error}",
            source=source,
        ).save()
