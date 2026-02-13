"""SAML Provider tasks"""

import requests
from django.contrib.auth import get_user_model
from dramatiq.actor import actor
from structlog.stdlib import get_logger

from authentik.events.models import Event, EventAction
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.providers.saml.processors.logout_request_parser import LogoutRequest
from authentik.providers.saml.processors.logout_response_processor import LogoutResponseProcessor

LOGGER = get_logger()
User = get_user_model()


@actor(description="Send SAML LogoutRequest to a Service Provider")
def send_saml_logout_request(
    provider_pk: int,
    sls_url: str,
    name_id: str,
    name_id_format: str,
    session_index: str,
):
    """Send SAML LogoutRequest to a Service Provider using session data"""
    provider = SAMLProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        LOGGER.error(
            "Provider not found for SAML logout request",
            provider_pk=provider_pk,
            session_index=session_index,
        )
        return False

    LOGGER.debug(
        "Sending SAML logout request",
        provider=provider.name,
        session_index=session_index,
    )

    # Note: We don't need the user object for the logout request itself
    processor = LogoutRequestProcessor(
        provider=provider,
        user=None,
        destination=sls_url,
        name_id=name_id,
        name_id_format=name_id_format,
        session_index=session_index,
    )

    return send_post_logout_request(provider, processor)


def send_post_logout_request(provider: SAMLProvider, processor: LogoutRequestProcessor) -> bool:
    """Send LogoutRequest using POST binding"""
    encoded_request = processor.encode_post()

    form_data = {
        "SAMLRequest": encoded_request,
    }

    if processor.relay_state:
        form_data["RelayState"] = processor.relay_state

    response = requests.post(
        provider.sls_url,
        data=form_data,
        timeout=10,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        allow_redirects=True,
    )
    response.raise_for_status()

    LOGGER.debug(
        "Sent POST logout request",
        provider=provider,
        status_code=response.status_code,
    )

    return True


@actor(description="Send SAML LogoutResponse to a Service Provider (backchannel)")
def send_saml_logout_response(
    provider_pk: int,
    sls_url: str,
    logout_request_id: str | None = None,
    relay_state: str | None = None,
):
    """Send SAML LogoutResponse to a Service Provider using backchannel (server-to-server)"""
    provider = SAMLProvider.objects.filter(pk=provider_pk).first()
    if not provider:
        LOGGER.error(
            "Provider not found for SAML logout response",
            provider_pk=provider_pk,
        )
        return False

    LOGGER.debug(
        "Sending backchannel SAML logout response",
        provider=provider.name,
        sls_url=sls_url,
    )

    # Create a minimal LogoutRequest object for the response processor
    # We only need the ID and relay_state for building the response
    logout_request = None
    if logout_request_id:
        logout_request = LogoutRequest()
        logout_request.id = logout_request_id
        logout_request.relay_state = relay_state

    # Build the logout response
    processor = LogoutResponseProcessor(
        provider=provider,
        logout_request=logout_request,
        destination=sls_url,
        relay_state=relay_state,
    )

    encoded_response = processor.encode_post()

    form_data = {
        "SAMLResponse": encoded_response,
    }

    if relay_state:
        form_data["RelayState"] = relay_state

    # Send the logout response to the SP
    try:
        response = requests.post(
            sls_url,
            data=form_data,
            timeout=10,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            allow_redirects=True,
        )
        response.raise_for_status()

        LOGGER.info(
            "Successfully sent backchannel logout response to SP",
            provider=provider.name,
            sls_url=sls_url,
            status_code=response.status_code,
        )
        return True

    except requests.exceptions.RequestException as exc:
        LOGGER.warning(
            "Failed to send backchannel logout response to SP",
            provider=provider.name,
            sls_url=sls_url,
            error=str(exc),
        )
        Event.new(
            EventAction.CONFIGURATION_ERROR,
            provider=provider,
            message=f"Backchannel logout response failed: {str(exc)}",
        ).save()
        return False
