"""authentik reputation request signals"""

from django.contrib.auth.signals import user_logged_in
from django.db.models import Case, F, Value, When
from django.db.models.functions import Greatest, Least
from django.dispatch import receiver
from django.http import HttpRequest
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from structlog.stdlib import get_logger

from authentik.core.signals import login_failed
from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.policies.reputation.models import Reputation, reputation_expiry
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.identification.signals import identification_failed
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


def update_score(request: HttpRequest, identifier: str, amount: int):
    """Update score for IP and User"""
    remote_ip = ClientIPMiddleware.get_client_ip(request)
    tenant = getattr(request, "tenant", get_current_tenant())
    amount = max(tenant.reputation_lower_limit, min(tenant.reputation_upper_limit, amount))

    with postgres_manager(Reputation) as manager:
        reputation = manager.on_conflict(
            ["ip", "identifier"],
            ConflictAction.UPDATE,
            update_values=dict(
                score=Greatest(
                    tenant.reputation_lower_limit,
                    Least(tenant.reputation_upper_limit, F("score") + amount),
                ),
            ),
        ).insert_and_get(
            ip=remote_ip,
            identifier=identifier,
            score=amount,
            ip_geo_data=GEOIP_CONTEXT_PROCESSOR.city_dict(remote_ip) or {},
            ip_asn_data=ASN_CONTEXT_PROCESSOR.asn_dict(remote_ip) or {},
            expires=reputation_expiry(),
        )

    LOGGER.info("Updated score", amount=reputation.score, for_user=identifier, for_ip=remote_ip)


def update_score_on_login(request: HttpRequest, identifier: str):
    """Update score for IP and User on a successful login: a negative score is reset
    to 0, any other score is raised by 1. Both branches happen in the same statement
    so that concurrent logins cannot race each other."""
    remote_ip = ClientIPMiddleware.get_client_ip(request)
    tenant = getattr(request, "tenant", get_current_tenant())
    initial = max(tenant.reputation_lower_limit, min(tenant.reputation_upper_limit, 1))

    with postgres_manager(Reputation) as manager:
        reputation = manager.on_conflict(
            ["ip", "identifier"],
            ConflictAction.UPDATE,
            update_values=dict(
                score=Greatest(
                    tenant.reputation_lower_limit,
                    Least(
                        tenant.reputation_upper_limit,
                        Case(
                            When(score__lt=0, then=Value(0)),
                            default=F("score") + 1,
                        ),
                    ),
                ),
            ),
        ).insert_and_get(
            ip=remote_ip,
            identifier=identifier,
            score=initial,
            ip_geo_data=GEOIP_CONTEXT_PROCESSOR.city_dict(remote_ip) or {},
            ip_asn_data=ASN_CONTEXT_PROCESSOR.asn_dict(remote_ip) or {},
            expires=reputation_expiry(),
        )

    LOGGER.info("Updated score", amount=reputation.score, for_user=identifier, for_ip=remote_ip)


@receiver(login_failed)
def handle_failed_login(sender, request, credentials, **_):
    """Lower Score for failed login attempts"""
    if "username" in credentials:
        update_score(request, credentials.get("username"), -1)


@receiver(identification_failed)
def handle_identification_failed(sender, request, uid_field: str, **_):
    """Lower Score for failed identification attempts"""
    update_score(request, uid_field, -1)


@receiver(user_logged_in)
def handle_successful_login(sender, request, user, **_):
    """Reset a negative score, otherwise raise it, for successful attempts"""
    update_score_on_login(request, user.username)
