from datetime import datetime
from uuid import uuid4

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
from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFProvider,
    Stream,
)
from authentik.enterprise.providers.ssf.tasks import send_ssf_event, ssf_push_request
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


@receiver(post_save, sender=Stream)
def ssf_stream_post_create(sender: type[Model], instance: Stream, created: bool, **_):
    """Send a verification event when a push stream is created"""
    if not created:
        return
    if instance.delivery_method != DeliveryMethods.RISC_PUSH:
        return
    ssf_push_request.delay(
        str(instance.uuid),
        instance.endpoint_url,
        {
            "jti": uuid4().hex,
            # TODO: Figure out how to get iss
            "iss": "https://ak.beryju.dev/.well-known/ssf-configuration/abm-ssf/8",
            "aud": instance.aud[0],
            "iat": int(datetime.now().timestamp()),
            "sub_id": {"format": "opaque", "id": str(instance.uuid)},
            "events": {
                "https://schemas.openid.net/secevent/ssf/event-type/verification": {
                    "state": None,
                }
            },
        },
    )


@receiver(user_logged_out)
def user_logged_out_session(sender, request: HttpRequest, user: User, **_):
    send_ssf_event.delay(
        EventTypes.SET_VERIFICATION,
        subject=get_user(user),
    )
