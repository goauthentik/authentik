"""OAuth2 Provider Tasks"""

from structlog.stdlib import get_logger

from authentik.core.models import AuthenticatedSession
from authentik.events.models import Event
from authentik.lib.utils.http import get_http_session
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.utils import create_logout_token
from authentik.root.celery import CELERY_APP

LOGGER = get_logger()


@CELERY_APP.task()
def send_backchannel_logout_request(
    provider_pk: int, iss: str, sub: str = None
) -> bool:
    """Send a back-channel logout request to the registered client

    Args:
        provider_pk: The OAuth2 provider's primary key
        sub: The subject identifier to include in the logout token

    Returns:
        bool: True if the request was sent successfully, False otherwise
    """
    if not sub:
        LOGGER.warning("No sub provided for back-channel logout")
        return False

    try:
        provider = OAuth2Provider.objects.get(pk=provider_pk)
    except OAuth2Provider.DoesNotExist:
        LOGGER.warning("Provider not found", provider_pk=provider_pk)
        return False

    # Generate the logout token
    try:
        logout_token = create_logout_token(iss, provider, None, sub)
    except Exception as exc:
        LOGGER.warning("Failed to create logout token", exc=exc)
        return False

    # Get the back-channel logout URI from the provider's dedicated backchannel_logout_uris field
    # Back-channel logout requires explicit configuration - no fallback to redirect URIs

    backchannel_logout_uri = None

    # Check if provider has dedicated backchannel logout URIs configured
    if provider.backchannel_logout_uris:
        # Use the first configured backchannel logout URI
        # In the future, we could implement logic to select based on criteria
        backchannel_logout_uri = provider.backchannel_logout_uris[0].url

    if not backchannel_logout_uri:
        LOGGER.warning(
            "No back-channel logout URI found for provider",
            provider=provider.name,
            client_id=provider.client_id,
        )
        return False

    # Send the back-channel logout request
    try:
        response = get_http_session().post(
            backchannel_logout_uri,
            data={"logout_token": logout_token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()

        # HTTP 200 OK is the expected response for successful back-channel logout
        HTTP_OK = 200
        if response.status_code == HTTP_OK:
            LOGGER.info(
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

        LOGGER.warning(
            "Back-channel logout failed",
            provider=provider.name,
            client_id=provider.client_id,
            status_code=response.status_code,
            response=response.text,
        )
        return False
    except Exception as exc:
        LOGGER.warning(
            "Error sending back-channel logout request",
            provider=provider.name,
            client_id=provider.client_id,
            exc=exc,
        )
        return False


def send_backchannel_logout_notification(session: AuthenticatedSession = None) -> None:
    """Send back-channel logout notifications to all relevant OAuth2 providers

    This function should be called when a user's session is terminated.

    Args:
        session: The authenticated session that was terminated
    """
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
    for token in access_tokens:
        # Send back-channel logout notifications to all tokens
        send_backchannel_logout_request.delay(
            provider_pk=token.provider.pk,
            iss=token.id_token.iss,
            sub=session.user.uid,
        )
