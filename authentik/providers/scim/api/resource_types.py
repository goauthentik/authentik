"""Serializers for SCIM resource-type diagnostics."""

from rest_framework.fields import BooleanField, CharField, ChoiceField, DateTimeField

from authentik.core.api.utils import PassiveSerializer


class SCIMResourceTypeExtensionSerializer(PassiveSerializer):
    """A schema extension advertised by the SCIM destination."""

    schema = CharField(source="schema_uri", read_only=True)
    required = BooleanField(read_only=True)


class SCIMResourceTypeSerializer(PassiveSerializer):
    """A resource type advertised by the SCIM destination."""

    id = CharField(allow_null=True, read_only=True)
    name = CharField(read_only=True)
    endpoint = CharField(read_only=True)
    description = CharField(allow_null=True, read_only=True)
    schema = CharField(source="schema_uri", read_only=True)
    schema_extensions = SCIMResourceTypeExtensionSerializer(many=True, read_only=True)


class SCIMResourceTypeDiscoverySerializer(PassiveSerializer):
    """Diagnostic result of querying the destination's ResourceTypes endpoint."""

    status = ChoiceField(choices=("success", "unavailable", "error"), read_only=True)
    resource_types = SCIMResourceTypeSerializer(many=True, read_only=True)
    fetched_at = DateTimeField(
        read_only=True, help_text="Time the discovery attempt completed, including failed attempts."
    )
    cached = BooleanField(read_only=True)
    detail = CharField(read_only=True)


class SCIMResourceTypeDiscoveryQuerySerializer(PassiveSerializer):
    """Options for on-demand resource-type discovery."""

    refresh = BooleanField(default=False, help_text="Bypass the cached discovery result.")
