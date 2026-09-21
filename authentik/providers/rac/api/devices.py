"""RAC Device API Views"""

from django.core.cache import cache
from django.db.models import Prefetch, QuerySet
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import mixins
from rest_framework.fields import CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.apps import AppAccessWithoutBindings
from authentik.core.models import Provider
from authentik.endpoints.models import Device, DeviceUserBinding
from authentik.policies.engine import PolicyEngine
from authentik.providers.rac.models import RACProvider, available_protocols, connection_override
from authentik.rbac.filters import ObjectFilter

LOGGER = get_logger()


def user_device_cache_key(user_pk: str, provider_pk: str) -> str:
    """Cache key where the accessible device list for a user is saved"""
    return f"goauthentik.io/providers/rac/device_access/{user_pk}/{provider_pk}"


class RACDeviceProtocolSerializer(PassiveSerializer):
    """A protocol a device can be connected to with"""

    protocol = CharField()
    launch_url = CharField(allow_null=True)


class RACDeviceSerializer(ModelSerializer):
    """Device as it can be launched through a RAC provider. Deliberately does not
    include any connection settings, as this is also used by end-users launching a
    connection."""

    protocols = SerializerMethodField()
    is_primary = SerializerMethodField()
    override_pk = SerializerMethodField()

    def get_override_pk(self, device: Device) -> int | None:
        """Primary key of this device's connection override, if it has one"""
        override = connection_override(device)
        return override.pk if override else None

    @property
    def provider(self) -> RACProvider:
        return self.context["rac_provider"]

    def get_is_primary(self, device: Device) -> bool:
        """Whether this is the requesting user's primary device"""
        return getattr(device, "is_primary", False)

    def get_protocols(self, device: Device) -> RACDeviceProtocolSerializer(many=True):
        """Protocols this device can be connected to with, and how to launch each"""
        return [
            {"protocol": protocol, "launch_url": self.launch_url(device, protocol)}
            for protocol in available_protocols(device)
        ]

    def launch_url(self, device: Device, protocol: str) -> str | None:
        """Build actual launch URL (the provider itself does not have one, just
        individual devices)"""
        try:
            return reverse(
                "authentik_providers_rac:start",
                kwargs={
                    "app": self.provider.application.slug,
                    "device": device.pk,
                    "protocol": protocol,
                },
            )
        except Provider.application.RelatedObjectDoesNotExist:
            return None

    class Meta:
        model = Device
        fields = [
            "device_uuid",
            "name",
            "protocols",
            "is_primary",
            "override_pk",
        ]


class RACDeviceViewSet(mixins.ListModelMixin, GenericViewSet):
    """Devices accessible through a RAC provider"""

    queryset = Device.objects.none()
    serializer_class = RACDeviceSerializer
    search_fields = ["name"]
    ordering = ["name"]
    filterset_fields = ["name"]

    def _filter_queryset_for_list(self, queryset: QuerySet) -> QuerySet:
        """Custom filter_queryset method which ignores guardian, but still supports sorting"""
        for backend in list(self.filter_backends):
            if backend == ObjectFilter:
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def _get_allowed_devices(self, provider: RACProvider, queryset: QuerySet) -> list[Device]:
        # A device is only reachable through the provider's application, so it must not
        # be listed to a user who has no access to that application - this mirrors the
        # launch flow (PolicyAccessView.user_has_access). Devices have no policy
        # bindings by default, so the per-device check alone would let any caller see
        # every device.
        try:
            application = provider.application
        except Provider.application.RelatedObjectDoesNotExist:
            return []
        app_engine = PolicyEngine(application, self.request.user, self.request)
        app_engine.empty_result = AppAccessWithoutBindings.get()
        app_engine.build()
        if not app_engine.passing:
            return []
        devices = []
        access_group_access: dict[str, bool] = {}
        for device in queryset:
            if device.access_group_id is not None:
                if device.access_group_id not in access_group_access:
                    group_engine = PolicyEngine(
                        device.access_group, self.request.user, self.request
                    )
                    group_engine.build()
                    access_group_access[device.access_group_id] = group_engine.passing
                if not access_group_access[device.access_group_id]:
                    continue
            # Bindings of users and groups to a device are policy bindings, so this
            # covers both device compliance policies and per-user access
            engine = PolicyEngine(device, self.request.user, self.request)
            engine.build()
            if not engine.passing:
                continue
            device.is_primary = any(
                binding.is_primary and binding.user_id == self.request.user.pk
                for binding in device.user_bindings
            )
            devices.append(device)
        return devices

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "provider",
                OpenApiTypes.INT,
                required=True,
            ),
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="superuser_full_list",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: RACDeviceSerializer(many=True),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    def list(self, request: Request, *args, **kwargs) -> Response:
        """List devices accessible through a RAC provider"""
        provider = RACProvider.objects.filter(pk=request.query_params.get("provider")).first()
        if not provider:
            return Response({"provider": "Valid provider required"}, status=400)
        self.rac_provider = provider

        queryset = self._filter_queryset_for_list(
            provider.devices()
            .select_related("rac_override")
            .prefetch_related(
                Prefetch(
                    "bindings", queryset=DeviceUserBinding.objects.all(), to_attr="user_bindings"
                )
            )
        )
        self.paginate_queryset(queryset)

        superuser_full_list = str(request.GET.get("superuser_full_list", "false")).lower() == "true"
        if superuser_full_list and request.user.is_superuser:
            allowed_devices = list(queryset)
        elif request.GET.get("search", "") != "":
            allowed_devices = self._get_allowed_devices(provider, queryset)
        else:
            allowed_devices = cache.get(user_device_cache_key(request.user.pk, provider.pk))
            if not allowed_devices:
                LOGGER.debug("Caching allowed device list")
                allowed_devices = self._get_allowed_devices(provider, queryset)
                cache.set(
                    user_device_cache_key(request.user.pk, provider.pk),
                    allowed_devices,
                    timeout=86400,
                )
        serializer = self.get_serializer(allowed_devices, many=True)
        return self.get_paginated_response(serializer.data)

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context["rac_provider"] = getattr(self, "rac_provider", None)
        return context
