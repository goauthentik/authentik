"""SAML Provider tasks"""

import requests
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest
from structlog.stdlib import get_logger

from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.events.models import Event, EventAction
from authentik.providers.saml.models import SAMLProvider
from authentik.providers.saml.processors.logout_request import LogoutRequestProcessor
from authentik.root.celery import CELERY_APP
from authentik.sources.saml.processors.constants import (
    SAML_NAME_ID_FORMAT_EMAIL,
    SAML_NAME_ID_FORMAT_PERSISTENT,
)

LOGGER = get_logger()
User = get_user_model()


@CELERY_APP.task()
def send_saml_logout_request(provider_pk: int, user_pk: int) -> bool:
    """Send SAML LogoutRequest to a Service Provider"""
    try:
        provider = SAMLProvider.objects.get(pk=provider_pk)
        user = User.objects.get(pk=user_pk)

        # Skip if no SLS URL configured
        if not provider.sls_url:
            LOGGER.debug("No SLS URL configured for provider", provider=provider)
            return True

        # Build LogoutRequest
        # Determine the NameID to use based on provider configuration
        name_id = user.uid  # Default to persistent ID
        name_id_format = SAML_NAME_ID_FORMAT_PERSISTENT

        # If provider has name_id_mapping, use that
        if provider.name_id_mapping:
            try:

                value = provider.name_id_mapping.evaluate(
                    user=user,
                    request=None,
                    provider=provider,
                )
                if value is not None:
                    name_id = str(value)
            except PropertyMappingExpressionException as exc:
                LOGGER.warning("Failed to evaluate name_id_mapping", exc=exc, provider=provider)
        else:
            # Without session context, we default to email for simplicity
            # In a real implementation, this should match what was used during authentication
            name_id = user.email
            name_id_format = SAML_NAME_ID_FORMAT_EMAIL

        processor = LogoutRequestProcessor(
            provider=provider,
            user=user,
            destination=provider.sls_url,
            name_id=name_id,
            name_id_format=name_id_format,
        )

        # Send POST logout request (only POST binding is supported for server-initiated logout)
        success = send_post_logout_request(provider, processor)

        # Log the event
        Event.new(
            EventAction.LOGOUT,
            provider=provider,
            user=user,
            message=f"SAML logout request {'sent' if success else 'failed'} to {provider.name}",
        ).save()

        return success

    except Exception as exc:
        LOGGER.error(
            "Failed to send SAML logout request", exc=exc, provider_pk=provider_pk, user_pk=user_pk
        )
        return False


def send_post_logout_request(provider: SAMLProvider, processor: LogoutRequestProcessor) -> bool:
    """Send LogoutRequest using POST binding"""
    try:
        encoded_request = processor.encode_post()

        # Create form data
        form_data = {
            "SAMLRequest": encoded_request,
        }

        # Send POST request
        response = requests.post(
            provider.sls_url,
            data=form_data,
            timeout=10,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        LOGGER.debug(
            "Sent POST logout request",
            provider=provider,
            status_code=response.status_code,
        )

        return response.status_code < HttpResponseBadRequest.status_code

    except Exception as exc:
        LOGGER.error("Failed to send POST logout request", exc=exc, provider=provider)
        return False
