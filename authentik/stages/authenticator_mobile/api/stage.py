"""AuthenticatorMobileStage API Views"""

from authentik_cloud_gateway_client.meta_pb2_grpc import MetaStub
from google.protobuf import empty_pb2
from grpc import RpcError
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_mobile.cloud_gateway import get_client
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage

LOGGER = get_logger()


class AuthenticatorMobileStageSerializer(StageSerializer):
    """AuthenticatorMobileStage Serializer"""

    def validate_cgw_endpoint(self, endpoint: str) -> str:
        """Validate connectivity and authentication to cgw"""
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            return endpoint
        client: MetaStub = get_client(endpoint, MetaStub)
        try:
            # pylint: disable=no-member
            client.Check(empty_pb2.Empty())
        except RpcError as exc:
            LOGGER.warning("failed to connect to cgw", error=exc)
            raise ValidationError("Failed to connect to cloud gateway")
        return endpoint

    class Meta:
        model = AuthenticatorMobileStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
            "item_matching_mode",
            "cgw_endpoint",
        ]


class AuthenticatorMobileStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorMobileStage Viewset"""

    queryset = AuthenticatorMobileStage.objects.all()
    serializer_class = AuthenticatorMobileStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]
