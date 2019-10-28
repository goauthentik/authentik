"""OIDC Permission checking"""
from django.contrib import messages
from django.shortcuts import redirect
from structlog import get_logger

from passbook.audit.models import Event
from passbook.core.models import Application
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()

def check_permissions(request, user, client):
    """Check permissions, used for
    https://django-oidc-provider.readthedocs.io/en/latest/
    sections/settings.html#oidc-after-userlogin-hook"""
    try:
        application = client.openidprovider.application
    except Application.DoesNotExist:
        return redirect('passbook_providers_oauth:oauth2-permission-denied')
    LOGGER.debug("Checking permissions for application", user=user, application=application)
    policy_engine = PolicyEngine(application.policies.all(), user, request)
    policy_engine.build()

    # Check permissions
    passing, policy_messages = policy_engine.result
    if not passing:
        for policy_message in policy_messages:
            messages.error(request, policy_message)
        return redirect('passbook_providers_oauth:oauth2-permission-denied')

    Event.create(
        action=Event.ACTION_AUTHORIZE_APPLICATION,
        request=request,
        app=application.name,
        skipped_authorization=False)
    return None
