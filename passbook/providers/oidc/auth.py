"""OIDC Permission checking"""
from typing import Optional

from django.contrib import messages
from django.db.models.deletion import Collector
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from oidc_provider.models import Client
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.core.models import Application, Provider, User
from passbook.flows.planner import FlowPlan
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.policies.engine import PolicyEngine

LOGGER = get_logger()


def client_related_provider(client: Client) -> Optional[Provider]:
    """Lookup related Application from Client"""
    # because oidc_provider is also used by app_gw, we can't be
    # sure an OpenIDProvider instance exists. hence we look through all related models
    # and choose the one that inherits from Provider, which is guaranteed to
    # have the application property
    collector = Collector(using="default")
    collector.collect([client])
    for _, related in collector.data.items():
        related_object = next(iter(related))
        if isinstance(related_object, Provider):
            return related_object
    return None


def check_permissions(
    request: HttpRequest, user: User, client: Client
) -> Optional[HttpResponse]:
    """Check permissions, used for
    https://django-oidc-provider.readthedocs.io/en/latest/
    sections/settings.html#oidc-after-userlogin-hook"""
    provider = client_related_provider(client)
    if not provider:
        return redirect("passbook_flows:denied")
    try:
        application = provider.application
    except Application.DoesNotExist:
        return redirect("passbook_flows:denied")
    LOGGER.debug(
        "Checking permissions for application", user=user, application=application
    )
    policy_engine = PolicyEngine(application, user, request)
    policy_engine.build()

    # Check permissions
    result = policy_engine.result
    if not result.passing:
        for policy_message in result.messages:
            messages.error(request, policy_message)
        return redirect("passbook_flows:denied")

    plan: FlowPlan = request.session[SESSION_KEY_PLAN]
    Event.new(
        EventAction.AUTHORIZE_APPLICATION,
        authorized_application=application,
        flow=plan.flow_pk,
    ).from_http(request)
    return None
