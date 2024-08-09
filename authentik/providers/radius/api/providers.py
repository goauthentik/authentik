"""RadiusProvider API Views"""

from base64 import b64encode

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from pyrad.dictionary import Attribute, Dictionary
from pyrad.packet import AuthPacket
from rest_framework.decorators import action
from rest_framework.fields import CharField, ListField
from rest_framework.mixins import ListModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.expression.exceptions import PropertyMappingExpressionException
from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.lib.expression.exceptions import ControlFlowException
from authentik.lib.sync.mapper import PropertyMappingManager
from authentik.lib.utils.errors import exception_to_string
from authentik.policies.api.exec import PolicyTestResultSerializer
from authentik.policies.engine import PolicyEngine
from authentik.policies.types import PolicyResult
from authentik.providers.radius.models import RadiusProvider, RadiusProviderPropertyMapping


class RadiusProviderSerializer(ProviderSerializer):
    """RadiusProvider Serializer"""

    outpost_set = ListField(child=CharField(), read_only=True, source="outpost_set.all")

    class Meta:
        model = RadiusProvider
        fields = ProviderSerializer.Meta.fields + [
            "client_networks",
            # Shared secret is not a write-only field, as
            # an admin might have to view it
            "shared_secret",
            "outpost_set",
            "mfa_support",
        ]
        extra_kwargs = ProviderSerializer.Meta.extra_kwargs


class RadiusProviderViewSet(UsedByMixin, ModelViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.all()
    serializer_class = RadiusProviderSerializer
    ordering = ["name"]
    search_fields = ["name", "client_networks"]
    filterset_fields = {
        "application": ["isnull"],
        "name": ["iexact"],
        "authorization_flow__slug": ["iexact"],
        "client_networks": ["iexact"],
    }


class RadiusOutpostConfigSerializer(ModelSerializer):
    """RadiusProvider Serializer"""

    application_slug = CharField(source="application.slug")
    auth_flow_slug = CharField(source="authorization_flow.slug")

    class Meta:
        model = RadiusProvider
        fields = [
            "pk",
            "name",
            "application_slug",
            "auth_flow_slug",
            "client_networks",
            "shared_secret",
            "mfa_support",
        ]


class RadiusOutpostConfigViewSet(ListModelMixin, GenericViewSet):
    """RadiusProvider Viewset"""

    queryset = RadiusProvider.objects.filter(application__isnull=False)
    serializer_class = RadiusOutpostConfigSerializer
    ordering = ["name"]
    search_fields = ["name"]
    filterset_fields = ["name"]

    class RadiusCheckAccessSerializer(PassiveSerializer):
        attributes = CharField(required=False)
        access = PolicyTestResultSerializer()

    def get_attributes(self, provider: RadiusProvider):
        mapper = PropertyMappingManager(
            provider.property_mappings.all().order_by("name").select_subclasses(),
            RadiusProviderPropertyMapping,
            ["packet"],
        )
        dict = Dictionary(
            str(
                settings.BASE_DIR
                / "authentik"
                / "providers"
                / "radius"
                / "dictionaries"
                / "dictionary"
            )
        )

        packet = AuthPacket()
        packet.secret = provider.shared_secret
        packet.dict = dict

        def define_attribute(
            vendor_code: int,
            vendor_name: str,
            attribute_name: str,
            attribute_code: int,
            attribute_type: str,
        ):
            """Dynamically add attribute to Radius packet"""
            # Ensure the vendor exists
            if vendor_code not in dict.vendors.backward or vendor_name not in dict.vendors.forward:
                dict.vendors.Add(vendor_name, vendor_code)
            full_attribute_name = f"{vendor_name}-{attribute_name}"
            if full_attribute_name not in dict.attributes:
                dict.attributes[full_attribute_name] = Attribute(
                    attribute_name, attribute_code, attribute_type, vendor=vendor_name
                )

        mapper.globals["define_attribute"] = define_attribute

        try:
            for _ in mapper.iter_eval(self.request.user, self.request, packet=packet):
                pass
        except (PropertyMappingExpressionException, ControlFlowException) as exc:
            # Value error can be raised when assigning invalid data to an attribute
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                message=f"Failed to evaluate property-mapping {exception_to_string(exc)}",
                mapping=exc.mapping,
            ).save()
            return None
        return b64encode(packet.RequestPacket()).decode()

    @extend_schema(
        request=None,
        parameters=[OpenApiParameter("app_slug", OpenApiTypes.STR)],
        responses={
            200: RadiusCheckAccessSerializer(),
        },
        operation_id="outposts_radius_access_check",
    )
    @action(detail=True)
    def check_access(self, request: Request, pk) -> Response:
        """Check access to a single application by slug"""
        provider = get_object_or_404(RadiusProvider, pk=pk)
        application = get_object_or_404(Application, slug=request.query_params["app_slug"])
        engine = PolicyEngine(application, request.user, request)
        engine.use_cache = False
        engine.build()
        result = engine.result
        access_response = PolicyResult(result.passing)
        attributes = None
        if result.passing:
            attributes = self.get_attributes(provider)
        response = self.RadiusCheckAccessSerializer(
            instance={
                "attributes": attributes,
                "access": access_response,
            }
        )
        return Response(response.data)
