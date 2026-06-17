"""authentik reputation request signals"""

from django.contrib.auth.signals import user_logged_in
from django.db.models import F
from django.db.models.functions import Greatest, Least
from django.dispatch import receiver
from django.http import HttpRequest
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager
from structlog.stdlib import get_logger

from authentik.admin.utils import get_system_settings
from authentik.core.signals import login_failed
from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.policies.reputation.models import Reputation, reputation_expiry
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.identification.signals import identification_failed

LOGGER = get_logger()


def update_score(request: HttpRequest, identifier: str, amount: int):
    """Update score for IP and User"""
    remote_ip = ClientIPMiddleware.get_client_ip(request)
    settings = get_system_settings()
    amount = max(settings.reputation_lower_limit, min(settings.reputation_upper_limit, amount))

    with postgres_manager(Reputation) as manager:
        reputation = manager.on_conflict(
            ["ip", "identifier"],
            ConflictAction.UPDATE,
            update_values=dict(
                score=Greatest(
                    settings.reputation_lower_limit,
                    Least(settings.reputation_upper_limit, F("score") + amount),
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
    """Raise score for successful attempts"""
    update_score(request, user.username, 1)
