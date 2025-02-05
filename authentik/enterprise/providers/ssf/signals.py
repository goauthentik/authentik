from hashlib import sha256

from django.contrib.auth.signals import user_logged_out
from django.db.models import Model
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver
from django.http.request import HttpRequest
from guardian.shortcuts import assign_perm

from authentik.core.models import (
    USER_PATH_SYSTEM_PREFIX,
    AuthenticatedSession,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.core.signals import password_changed
from authentik.enterprise.providers.ssf.models import (
    EventTypes,
    SSFProvider,
)
from authentik.enterprise.providers.ssf.tasks import send_ssf_event
from authentik.events.middleware import audit_ignore
from authentik.stages.authenticator.models import Device
from authentik.stages.authenticator_duo.models import DuoDevice
from authentik.stages.authenticator_static.models import StaticDevice
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    WebAuthnDevice,
)

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
    assign_perm("add_stream", user, instance)
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
def ssf_user_logged_out_session_revoked(sender, request: HttpRequest, user: User, **_):
    """Session revoked trigger (user logged out)"""
    if not request.session or not request.session.session_key or not user:
        return
    send_ssf_event(
        EventTypes.CAEP_SESSION_REVOKED,
        {
            "subject": {
                "session": {
                    "format": "opaque",
                    "id": sha256(request.session.session_key.encode("ascii")).hexdigest(),
                },
                "user": {
                    "format": "email",
                    "email": user.email,
                },
            },
            "initiating_entity": "user",
        },
        request=request,
    )


@receiver(pre_delete, sender=AuthenticatedSession)
def ssf_user_session_delete_session_revoked(sender, instance: AuthenticatedSession, **_):
    """Session revoked trigger (users' session has been deleted)

    As this signal is also triggered with a regular logout, we can't be sure
    if the session has been deleted by an admin or by the user themselves."""
    send_ssf_event(
        EventTypes.CAEP_SESSION_REVOKED,
        {
            "subject": {
                "session": {
                    "format": "opaque",
                    "id": sha256(instance.session_key.encode("ascii")).hexdigest(),
                },
                "user": {
                    "format": "email",
                    "email": instance.user.email,
                },
            },
            "initiating_entity": "user",
        },
    )


@receiver(password_changed)
def ssf_password_changed_cred_change(sender, user: User, password: str | None, **_):
    """Credential change trigger (password changed)"""
    send_ssf_event(
        EventTypes.CAEP_CREDENTIAL_CHANGE,
        {
            "subject": {
                "user": {
                    "format": "email",
                    "email": user.email,
                },
            },
            "credential_type": "password",
            "change_type": "revoke" if password is None else "update",
        },
    )


device_type_map = {
    StaticDevice: "pin",
    TOTPDevice: "pin",
    WebAuthnDevice: "fido-u2f",
    DuoDevice: "app",
}


@receiver(post_save)
def ssf_device_post_save(sender: type[Model], instance: Device, created: bool, **_):
    if not isinstance(instance, Device):
        return
    if not instance.confirmed:
        return
    device_type = device_type_map.get(instance.__class__)
    data = {
        "subject": {
            "user": {
                "format": "email",
                "email": instance.user.email,
            },
        },
        "credential_type": device_type,
        "change_type": "create" if created else "update",
        "friendly_name": instance.name,
    }
    if isinstance(instance, WebAuthnDevice) and instance.aaguid != UNKNOWN_DEVICE_TYPE_AAGUID:
        data["fido2_aaguid"] = instance.aaguid
    send_ssf_event(EventTypes.CAEP_CREDENTIAL_CHANGE, data)


@receiver(post_delete)
def ssf_device_post_delete(sender: type[Model], instance: Device, **_):
    if not isinstance(instance, Device):
        return
    if not instance.confirmed:
        return
    device_type = device_type_map.get(instance.__class__)
    data = {
        "subject": {
            "user": {
                "format": "email",
                "email": instance.user.email,
            },
        },
        "credential_type": device_type,
        "change_type": "delete",
        "friendly_name": instance.name,
    }
    if isinstance(instance, WebAuthnDevice) and instance.aaguid != UNKNOWN_DEVICE_TYPE_AAGUID:
        data["fido2_aaguid"] = instance.aaguid
    send_ssf_event(EventTypes.CAEP_CREDENTIAL_CHANGE, data)
