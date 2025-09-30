"""OAuth2 Provider Tasks"""

from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.lib.utils.http import get_http_session
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.utils import create_logout_token
from authentik.tasks.models import Task

LOGGER = get_logger()


@actor(description=_("Send a back-channel logout request to the registered client"))
def send_backchannel_logout_request(
    provider_pk: int,
    iss: str,
    sub: str | None = None,
    session_key: str | None = None,
) -> bool:
    """Send a back-channel logout request to the registered client

    Args:
        provider_pk: The OAuth2 provider's primary key
        iss: The issuer URL for the logout token
        sub: The subject identifier to include in the logout token
        session_key: The authentik session key to hash and include in the logout token

    Returns:
        bool: True if the request was sent successfully, False otherwise
    """
    self: Task = CurrentTask.get_task()
    LOGGER.debug("Sending back-channel logout request", provider_pk=provider_pk, sub=sub)

    provider = OAuth2Provider.objects.filter(pk=provider_pk).first()
    if provider is None:
        return

    # Generate the logout token
    logout_token = create_logout_token(provider, iss, sub, session_key)

    # Get the back-channel logout URI from the provider's dedicated backchannel_logout_uri field
    # Back-channel logout requires explicit configuration - no fallback to redirect URIs
    backchannel_logout_uri = provider.backchannel_logout_uri
    if not backchannel_logout_uri:
        self.info("No back-channel logout URI found for provider")
        return

    # Send the back-channel logout request
    response = get_http_session().post(
        backchannel_logout_uri,
        data={"logout_token": logout_token},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=True,
    )
    response.raise_for_status()

    self.info("Back-channel logout successful", sub=sub)
    return True


@actor(description=_("Handle backchannel logout notifications dispatched via signal"))
def backchannel_logout_notification_dispatch(revocations: list, **kwargs):
    """Handle backchannel logout notifications dispatched via signal"""
    for revocation in revocations:
        provider_pk, iss, sub, session_key = revocation
        provider = OAuth2Provider.objects.filter(pk=provider_pk).first()
        send_backchannel_logout_request.send_with_options(
            args=(provider_pk, iss, sub, session_key),
            rel_obj=provider,
        )
