"""GETTING REMOVED WHEN FRONTEND IS DONE: support the old admin forms."""

from json import dumps

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework.fields import CharField, JSONField, SkipField, empty
from rest_framework.serializers import ValidationError

# GETTING REMOVED WHEN FRONTEND IS DONE, including the ModelSerializer hooks.
LEGACY_FIELDS = {
    "authentik_endpoints_connectors_fleet.fleetconnector": [
        ["_token", "secret", True, False, None]
    ],
    "authentik_endpoints_connectors_google_chrome.googlechromeconnector": [
        ["credentials", "secret", False, True, "multiline"]
    ],
    "authentik_providers_google_workspace.googleworkspaceprovider": [
        ["credentials", "secret", False, True, "multiline"]
    ],
    "authentik_providers_microsoft_entra.microsoftentraprovider": [
        ["_client_secret", "secret", True, False, None]
    ],
    "authentik_stages_authenticator_endpoint_gdtc.authenticatorendpointgdtcstage": [
        ["credentials", "secret", False, True, "multiline"]
    ],
    "authentik_events.notificationtransport": [["_webhook_url", "secret", False, False, None]],
    "authentik_outposts.kubernetesserviceconnection": [
        ["kubeconfig", "secret", False, True, "multiline"]
    ],
    "authentik_providers_oauth2.oauth2provider": [["_client_secret", "secret", False, False, None]],
    "authentik_providers_radius.radiusprovider": [["_shared_secret", "secret", False, False, None]],
    "authentik_providers_scim.scimprovider": [["_token", "secret", True, False, None]],
    "authentik_sources_kerberos.kerberossource": [
        ["_sync_password", "secret", True, False, None],
        ["sync_keytab", "sync_keytab_secret", True, False, "file"],
        ["sync_ccache", "sync_ccache_secret", True, False, "file"],
        ["spnego_keytab", "spnego_keytab_secret", True, False, "file"],
        ["spnego_ccache", "spnego_ccache_secret", True, False, "file"],
    ],
    "authentik_sources_ldap.ldapsource": [["_bind_password", "secret", True, False, None]],
    "authentik_sources_oauth.oauthsource": [["_consumer_secret", "secret", True, False, None]],
    "authentik_sources_plex.plexsource": [["_plex_token", "secret", False, False, None]],
    "authentik_sources_telegram.telegramsource": [["_bot_token", "secret", True, False, None]],
    "authentik_stages_authenticator_duo.authenticatorduostage": [
        ["_client_secret", "secret", True, False, None],
        ["_admin_secret_key", "admin_secret", True, False, None],
    ],
    "authentik_stages_authenticator_email.authenticatoremailstage": [
        ["_password", "secret", True, False, None]
    ],
    "authentik_stages_authenticator_sms.authenticatorsmsstage": [
        ["_auth", "auth_secret", True, False, None],
        ["_auth_password", "auth_password_secret", True, False, None],
    ],
    "authentik_stages_captcha.captchastage": [["_private_key", "secret", True, False, None]],
    "authentik_stages_email.emailstage": [["_password", "secret", True, False, None]],
}


class LegacySecretField(CharField):
    """Translate a literal credential to a new, unsaved secret."""

    def __init__(self, *args, secret_type=None, **kwargs):
        self.secret_type = secret_type
        super().__init__(*args, **kwargs)

    def run_validation(self, data=empty):
        from authentik.crypto.secrets.models import Secret, SecretType

        if data is not empty and self.source in self.parent.initial_data:
            raise ValidationError(_("Provide either the credential or its secret reference."))
        value = super().run_validation(data)
        if value == "":
            raise SkipField
        secret = Secret(
            value=value,
            type=self.secret_type or (SecretType.MULTILINE if "\n" in value else SecretType.TEXT),
        )
        validate = getattr(self.parent, f"validate_{self.source}", None)
        return validate(secret) if validate else secret

    def get_attribute(self, instance):
        from authentik.events.models import Event, EventAction

        request = self.context.get("request")
        if not request or (
            request.method != "GET"
            and self.field_name not in getattr(self.parent, "initial_data", {})
        ):
            raise SkipField
        secret = super().get_attribute(instance)
        if not secret or not (
            request.user.has_perm("authentik_secrets.view_secret_value")
            or request.user.has_perm("authentik_secrets.view_secret_value", secret)
        ):
            raise SkipField
        Event.new(EventAction.SECRET_VIEW, secret=secret).from_http(request)
        return secret

    def to_representation(self, value):
        return value.value


@extend_schema_field(OpenApiTypes.OBJECT)
class LegacyJSONSecretField(LegacySecretField):
    def run_validation(self, data=empty):
        if data is not empty:
            data = JSONField().run_validation(data)
            if not isinstance(data, dict):
                raise ValidationError(_("Credential must be a JSON or YAML object."))
            data = dumps(data)
        return super().run_validation(data)

    def to_representation(self, value):
        return value.get_json()


class LegacySecretCompatibility:
    # GETTING REMOVED WHEN FRONTEND IS DONE: retain literal credential inputs.

    def get_fields(self):
        fields = super().get_fields()
        for old, new, write_only, structured, secret_type in LEGACY_FIELDS.get(
            self.Meta.model._meta.label_lower, []
        ):
            if new not in fields:
                continue
            old_field = self.Meta.model._meta.get_field(old)
            name = old.lstrip("_")
            field_type = LegacyJSONSecretField if structured else LegacySecretField
            fields[name] = field_type(
                source=new,
                required=False,
                write_only=write_only,
                allow_blank=old_field.blank,
                trim_whitespace=False,
                max_length=old_field.max_length,
                secret_type=secret_type,
            )
            if name in getattr(self, "initial_data", {}):
                fields[new].required = False
        return fields

    def prepare_legacy_credentials(self, instance, validated_data):
        from authentik.crypto.secrets.models import Secret, create_named_secret

        for name, value in tuple(validated_data.items()):
            if not isinstance(value, Secret) or not value._state.adding:
                continue
            current = getattr(instance, name, None)
            if current and current.value == value.value and current.type == value.type:
                validated_data[name] = current
                continue
            # Old forms edit one consumer; never rotate a credential shared with another.
            consumer_name = validated_data.get("name", getattr(instance, "name", ""))
            secret = create_named_secret(f"{consumer_name} {name.replace('_', ' ')}")
            secret.value, secret.type = value.value, value.type
            secret.save(update_fields=["value", "type"])
            request = self.context.get("request")
            if request:
                permissions = ["view_secret", "change_secret", "rotate_secret"]
                if any(
                    isinstance(field, LegacySecretField)
                    and field.source == name
                    and not field.write_only
                    for field in self.fields.values()
                ):
                    permissions.append("view_secret_value")
                request.user.assign_perms_to_managed_role(
                    [f"authentik_secrets.{permission}" for permission in permissions], secret
                )
            validated_data[name] = secret
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(self.prepare_legacy_credentials(None, validated_data))
