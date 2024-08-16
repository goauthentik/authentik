from django.contrib.auth.signals import user_logged_out
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http.request import HttpRequest

from authentik.core.models import (
    USER_PATH_SYSTEM_PREFIX,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.enterprise.providers.ssf.models import EventTypes, SSFProvider
from authentik.enterprise.providers.ssf.tasks import send_ssf_event
from authentik.events.middleware import audit_ignore
from authentik.events.utils import get_user

USER_PATH_PROVIDERS_SSF = USER_PATH_SYSTEM_PREFIX + "/providers/ssf"


@receiver(post_save, sender=SSFProvider)
def ssf_providers_post_save(sender: type[Model], instance: SSFProvider, created: bool, **_):
    """Create service account before provider is saved"""
    identifier = instance.service_account_identifier
    user, _ = User.objects.update_or_create(
        username=identifier,
        defaults={
            "name": f"SSF Provider {instance.name} Service-Account",
            "type": UserTypes.INTERNAL_SERVICE_ACCOUNT,
            "path": USER_PATH_PROVIDERS_SSF,
        },
    )
    token, token_created = Token.objects.update_or_create(
        identifier=identifier,
        defaults={
            "user": user,
            "intent": TokenIntents.INTENT_API,
            "expiring": False,
            "managed": f"goauthentik.io/providers/ssf/{instance.pk}",
        },
    )
    if created or token_created:
        with audit_ignore():
            instance.token = token
            instance.save()


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    send_ssf_event.delay(
        EventTypes.CAEP_SESSION_REVOKED,
        subject=get_user(user),
    )
