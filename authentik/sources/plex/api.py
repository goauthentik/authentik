"""Plex Source Serializer"""
from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.sources import SourceSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.flows.challenge import RedirectChallenge
from authentik.flows.views import to_stage_response
from authentik.sources.plex.models import PlexSource
from authentik.sources.plex.plex import PlexAuth


class PlexSourceSerializer(SourceSerializer):
    """Plex Source Serializer"""

    class Meta:
        model = PlexSource
        fields = SourceSerializer.Meta.fields + ["client_id", "allowed_servers"]


class PlexTokenRedeemSerializer(PassiveSerializer):
    """Serializer to redeem a plex token"""

    plex_token = CharField()


class PlexSourceViewSet(ModelViewSet):
    """Plex source Viewset"""

    queryset = PlexSource.objects.all()
    serializer_class = PlexSourceSerializer
    lookup_field = "slug"

    @permission_required(None)
    @swagger_auto_schema(
        request_body=PlexTokenRedeemSerializer(),
        responses={200: RedirectChallenge(), 404: "Token not found"},
        manual_parameters=[
            openapi.Parameter(
                name="slug",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
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
            raise Http404
        auth_api = PlexAuth(source, plex_token)
        if not auth_api.check_server_overlap():
            raise Http404
        response = auth_api.get_user_url(request)
        return to_stage_response(request, response)
