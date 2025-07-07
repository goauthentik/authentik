"""authentik reputation request signals"""

from django.contrib.auth.signals import user_logged_in
from django.db import transaction
from django.dispatch import receiver
from django.http import HttpRequest
from structlog.stdlib import get_logger

from authentik.core.signals import login_failed
from authentik.events.context_processors.asn import ASN_CONTEXT_PROCESSOR
from authentik.events.context_processors.geoip import GEOIP_CONTEXT_PROCESSOR
from authentik.policies.reputation.models import Reputation, reputation_expiry
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.identification.signals import identification_failed
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


def clamp(value, min, max):
    return sorted([min, value, max])[1]


def update_score(request: HttpRequest, identifier: str, amount: int):
    """Update score for IP and User"""
    remote_ip = ClientIPMiddleware.get_client_ip(request)
    tenant = get_current_tenant()
    new_score = clamp(amount, tenant.reputation_lower_limit, tenant.reputation_upper_limit)

    with transaction.atomic():
        reputation, created = Reputation.objects.select_for_update().get_or_create(
            ip=remote_ip,
            identifier=identifier,
            defaults={
                "score": clamp(
                    amount, tenant.reputation_lower_limit, tenant.reputation_upper_limit
                ),
                "ip_geo_data": GEOIP_CONTEXT_PROCESSOR.city_dict(remote_ip) or {},
                "ip_asn_data": ASN_CONTEXT_PROCESSOR.asn_dict(remote_ip) or {},
                "expires": reputation_expiry(),
            },
        )

        if not created:
            new_score = clamp(
                reputation.score + amount,
                tenant.reputation_lower_limit,
                tenant.reputation_upper_limit,
            )
            reputation.score = new_score
            reputation.save()

    LOGGER.info("Updated score", amount=new_score, for_user=identifier, for_ip=remote_ip)


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
