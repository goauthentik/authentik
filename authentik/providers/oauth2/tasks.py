"""OAuth2 Provider Tasks"""

from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession
from authentik.events.models import Event
from authentik.lib.utils.http import get_http_session
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.utils import create_logout_token
from authentik.tasks.models import Task

LOGGER = get_logger()


@actor(description=_("Send a back-channel logout request to the registered client"))
def send_backchannel_logout_request(provider_pk: int, iss: str, sub: str = None) -> bool:
    """Send a back-channel logout request to the registered client

    Args:
        provider_pk: The OAuth2 provider's primary key
        iss: The issuer URL for the logout token
        sub: The subject identifier to include in the logout token

    Returns:
        bool: True if the request was sent successfully, False otherwise
    """
    self: Task = CurrentTask.get_task()
    LOGGER.debug("Sending back-channel logout request", provider_pk=provider_pk, sub=sub)

    provider = OAuth2Provider.objects.filter(pk=provider_pk).first()
    if provider is None:
        return

    # Generate the logout token
    logout_token = create_logout_token(iss, provider, None, sub)

    # Get the back-channel logout URI from the provider's dedicated backchannel_logout_uri field
    # Back-channel logout requires explicit configuration - no fallback to redirect URIs

    backchannel_logout_uri = provider.backchannel_logout_uri
    if not backchannel_logout_uri:
        self.info(
            "No back-channel logout URI found for provider",
            provider=provider.name,
            client_id=provider.client_id,
        )
        return

    # Send the back-channel logout request
    response = get_http_session().post(
        backchannel_logout_uri,
        data={"logout_token": logout_token},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    self.info(
        "Back-channel logout successful",
        provider=provider.name,
        client_id=provider.client_id,
        sub=sub,
    )
    Event.new(
        "backchannel_logout",
        message="Back-channel logout notification sent",
        provider=provider,
        client_id=provider.client_id,
        sub=sub,
    ).save()
    return True


@actor()
def backchannel_logout_notification_dispatch(revocations: list, **kwargs):
    """Handle backchannel logout notifications dispatched via signal"""
    for revocation in revocations:
        provider_pk, iss, sub = revocation
        provider = OAuth2Provider.objects.filter(pk=provider_pk).first()
        send_backchannel_logout_request.send_with_options(
            args=(provider_pk, iss, sub),
            rel_obj=provider,
        )


def send_backchannel_logout_notification(session: AuthenticatedSession = None) -> None:
    """Send back-channel logout notifications to all relevant OAuth2 providers

    This function should be called when a user's session is terminated.

    Args:
        session: The authenticated session that was terminated
    """
    LOGGER.debug("Sending back-channel logout notifications for session", session=session)
    if not session:
        LOGGER.warning("No session provided for back-channel logout notification")
        return

    # Per OpenID Connect Back-Channel Logout 1.0 spec section 2.3:
    # "OPs supporting back-channel logout need to keep track of the set of logged-in RPs"
    # We track all OAuth2 providers that have active sessions with the user,
    # regardless of token type or flow (authorization code, implicit, hybrid)
    # Refresh tokens issued without the offline_access property to a session being logged out
    # SHOULD be revoked. Refresh tokens issued with the offline_access property
    # normally SHOULD NOT be revoked.
    from authentik.providers.oauth2.models import AccessToken

    # Get all OAuth2 providers that have issued tokens for this session
    access_tokens = AccessToken.objects.select_related("provider").filter(session=session)
    LOGGER.debug(
        "back-channel: Found access tokens for session",
        session=session,
        access_tokens=access_tokens,
    )
    for token in access_tokens:
        LOGGER.debug(
            "back-channel: Sending back-channel logout notification for token", token=token
        )
        # Send back-channel logout notifications to all tokens
        send_backchannel_logout_request.send(
            provider_pk=token.provider.pk,
            iss=token.id_token.iss,
            sub=token.id_token.sub,
        )
