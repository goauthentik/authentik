"""Outpost API Views"""
from dacite.core import from_dict
from dacite.exceptions import DaciteError
from django_filters.filters import ModelMultipleChoiceFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, DateTimeField
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import JSONField, ModelSerializer, ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik import get_build_hash
from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer, is_dict
from authentik.core.models import Provider
from authentik.outposts.api.service_connections import ServiceConnectionSerializer
from authentik.outposts.apps import MANAGED_OUTPOST
from authentik.outposts.models import (
    Outpost,
    OutpostConfig,
    OutpostState,
    OutpostType,
    default_outpost_config,
)
from authentik.providers.ldap.models import LDAPProvider
from authentik.providers.proxy.models import ProxyProvider
from authentik.providers.radius.models import RadiusProvider


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    config = JSONField(validators=[is_dict], source="_config")
    # Need to set allow_empty=True for the embedded outpost with no providers
    # is checked for other providers in the API Viewset
    providers = PrimaryKeyRelatedField(
        allow_empty=True,
        many=True,
        queryset=Provider.objects.select_subclasses().all(),
    )
    providers_obj = ProviderSerializer(source="providers", many=True, read_only=True)
    service_connection_obj = ServiceConnectionSerializer(
        source="service_connection", read_only=True
    )

    def validate_providers(self, providers: list[Provider]) -> list[Provider]:
        """Check that all providers match the type of the outpost"""
        type_map = {
            OutpostType.LDAP: LDAPProvider,
            OutpostType.PROXY: ProxyProvider,
            OutpostType.RADIUS: RadiusProvider,
            None: Provider,
        }
        for provider in providers:
            if not isinstance(provider, type_map[self.initial_data.get("type")]):
                raise ValidationError(
                    f"Outpost type {self.initial_data['type']} can't be used with "
                    f"{provider.__class__.__name__} providers."
                )
        if self.instance and self.instance.managed == MANAGED_OUTPOST:
            return providers
        if len(providers) < 1:
            raise ValidationError("This list may not be empty.")
        return providers

    def validate_config(self, config) -> dict:
        """Check that the config has all required fields"""
        try:
            from_dict(OutpostConfig, config)
        except DaciteError as exc:
            raise ValidationError(f"Failed to validate config: {str(exc)}") from exc
        return config

    class Meta:
        model = Outpost
        fields = [
            "pk",
            "name",
            "type",
            "providers",
            "providers_obj",
            "service_connection",
            "service_connection_obj",
            "token_identifier",
            "config",
            "managed",
        ]
        extra_kwargs = {"type": {"required": True}}


class OutpostDefaultConfigSerializer(PassiveSerializer):
    """Global default outpost config"""

    config = JSONField(read_only=True)


class OutpostHealthSerializer(PassiveSerializer):
    """Outpost health status"""

    uid = CharField(read_only=True)
    last_seen = DateTimeField(read_only=True)
    version = CharField(read_only=True)
    version_should = CharField(read_only=True)

    version_outdated = BooleanField(read_only=True)

    build_hash = CharField(read_only=True, required=False)
    build_hash_should = CharField(read_only=True, required=False)

    hostname = CharField(read_only=True, required=False)


class OutpostFilter(FilterSet):
    """Filter for Outposts"""

    providers_by_pk = ModelMultipleChoiceFilter(
        field_name="providers",
        queryset=Provider.objects.all(),
    )

    class Meta:
        model = Outpost
        fields = {
            "providers": ["isnull"],
            "name": ["iexact", "icontains"],
            "service_connection__name": ["iexact", "icontains"],
            "managed": ["iexact", "icontains"],
        }


class OutpostViewSet(UsedByMixin, ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer
    filterset_class = OutpostFilter
    search_fields = [
        "name",
        "providers__name",
    ]
    ordering = ["name", "service_connection__name"]

    @extend_schema(responses={200: OutpostHealthSerializer(many=True)})
    @action(methods=["GET"], detail=True, pagination_class=None)
    def health(self, request: Request, pk: int) -> Response:
        """Get outposts current health"""
        outpost: Outpost = self.get_object()
        states = []
        for state in outpost.state:
            state: OutpostState
            states.append(
                {
                    "uid": state.uid,
                    "last_seen": state.last_seen,
                    "version": state.version,
                    "version_should": state.version_should,
                    "version_outdated": state.version_outdated,
                    "build_hash": state.build_hash,
                    "hostname": state.hostname,
                    "build_hash_should": get_build_hash(),
                }
            )
        return Response(OutpostHealthSerializer(states, many=True).data)

    @extend_schema(responses={200: OutpostDefaultConfigSerializer(many=False)})
    @action(detail=False, methods=["GET"])
    def default_settings(self, request: Request) -> Response:
        """Global default outpost config"""
        host = self.request.build_absolute_uri("/")
        return Response({"config": default_outpost_config(host)})
