"""Plex Source Serializer"""
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import CharField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.views import to_stage_response
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth, PlexSourceFlowManager

LOGGER = get_logger()


class PlexSourceSerializer(SourceSerializer):
    """Plex Source Serializer"""

    class Meta:
        model = PlexSource
        fields = SourceSerializer.Meta.fields + [
            "client_id",
            "allowed_servers",
            "allow_friends",
            "plex_token",
        ]


class PlexTokenRedeemSerializer(PassiveSerializer):
    """Serializer to redeem a plex token"""

    plex_token = CharField()


class PlexSourceViewSet(UsedByMixin, ModelViewSet):
    """Plex source Viewset"""

    queryset = PlexSource.objects.all()
    serializer_class = PlexSourceSerializer
    lookup_field = "slug"
    filterset_fields = [
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "policy_engine_mode",
        "user_matching_mode",
        "client_id",
        "allow_friends",
    ]
    ordering = ["name"]

    @permission_required(None)
    @extend_schema(
        request=PlexTokenRedeemSerializer(),
        responses={
            200: RedirectChallenge(),
            400: OpenApiResponse(description="Token not found"),
            403: OpenApiResponse(description="Access denied"),
        },
        parameters=[
            OpenApiParameter(
                name="slug",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
            )
        ],
    )
    @action(
        methods=["POST"],
        detail=False,
        pagination_class=None,
        filter_backends=[],
        permission_classes=[AllowAny],
    )
    def redeem_token(self, request: Request) -> Response:
        """Redeem a plex token, check it's access to resources against what's allowed
        for the source, and redirect to an authentication/enrollment flow."""
        source: PlexSource = get_object_or_404(
            PlexSource, slug=request.query_params.get("slug", "")
        )
        plex_token = request.data.get("plex_token", None)
        if not plex_token:
            raise ValidationError("No plex token given")
        auth_api = PlexAuth(source, plex_token)
        user_info, identifier = auth_api.get_user_info()
        # Check friendship first, then check server overlay
        friends_allowed = False
        owner_id = None
        if source.allow_friends:
            owner_api = PlexAuth(source, source.plex_token)
            owner_id = owner_api.get_user_info
            owner_friends = owner_api.get_friends()
            for friend in owner_friends:
                if int(friend.get("id", "0")) == int(identifier):
                    friends_allowed = True
                    LOGGER.info(
                        "allowing user for plex because of friend",
                        user=user_info["username"],
                    )
        servers_allowed = auth_api.check_server_overlap()
        owner_allowed = owner_id == identifier
        if any([friends_allowed, servers_allowed, owner_allowed]):
            sfm = PlexSourceFlowManager(
                source=source,
                request=request,
                identifier=str(identifier),
                enroll_info=user_info,
            )
            return to_stage_response(request, sfm.get_flow(plex_token=plex_token))
        LOGGER.warning(
            "Denying plex auth because no server overlay and no friends and not owner",
            user=user_info["username"],
        )
        raise PermissionDenied("Access denied.")
