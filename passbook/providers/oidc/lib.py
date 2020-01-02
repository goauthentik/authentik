"""OIDC Permission checking"""
from typing import Optional

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from oidc_provider.models import Client
from structlog import get_logger
from django.db.models.deletion import Collector

from passbook.audit.models import Event, EventAction
from passbook.core.models import Application, User, Provider
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()


def check_permissions(
    request: HttpRequest, user: User, client: Client
) -> Optional[HttpResponse]:
    """Check permissions, used for
    https://django-oidc-provider.readthedocs.io/en/latest/
    sections/settings.html#oidc-after-userlogin-hook"""
    try:
        # because oidc_provider is also used by app_gw, we can't be
        # sure an OpenIDPRovider instance exists. hence we look through all related models
        # and choose the one that inherits from Provider, which is guaranteed to
        # have the application property
        collector = Collector(using="default")
        collector.collect([client])
        for _, related in collector.data.items():
            related_object = next(iter(related))
            if isinstance(related_object, Provider):
                application = related.application
                break
    except Application.DoesNotExist:
        return redirect("passbook_providers_oauth:oauth2-permission-denied")
    LOGGER.debug(
        "Checking permissions for application", user=user, application=application
    )
    policy_engine = PolicyEngine(application.policies.all(), user, request)
    policy_engine.build()

    # Check permissions
    passing, policy_messages = policy_engine.result
    if not passing:
        for policy_message in policy_messages:
            messages.error(request, policy_message)
        return redirect("passbook_providers_oauth:oauth2-permission-denied")

    Event.new(
        EventAction.AUTHORIZE_APPLICATION,
        authorized_application=application,
        skipped_authorization=False,
    ).from_http(request)
    return None
