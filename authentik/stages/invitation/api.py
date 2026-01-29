"""Invitation Stage API Views"""

from smtplib import SMTPException

from django.http import HttpRequest
from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from drf_spectacular.utils import extend_schema
from guardian.shortcuts import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    CharField,
    ListField,
    PrimaryKeyRelatedField,
    Serializer,
    ValidationError,
)
from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import JSONDictField, ModelSerializer
from authentik.core.models import User
from authentik.flows.api.flows import FlowSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.stages.invitation.models import Invitation, InvitationStage

LOGGER = get_logger()


class InvitationStageSerializer(StageSerializer):
    """InvitationStage Serializer"""

    class Meta:
        model = InvitationStage
        fields = StageSerializer.Meta.fields + [
            "continue_flow_without_invitation",
        ]


class InvitationStageFilter(FilterSet):
    """invitation filter"""

    no_flows = BooleanFilter("flow", "isnull")

    class Meta:
        model = InvitationStage
        fields = ["name", "no_flows", "continue_flow_without_invitation", "stage_uuid"]


class InvitationStageViewSet(UsedByMixin, ModelViewSet):
    """InvitationStage Viewset"""

    queryset = InvitationStage.objects.all()
    serializer_class = InvitationStageSerializer
    filterset_class = InvitationStageFilter
    ordering = ["name"]
    search_fields = ["name"]


class InvitationSerializer(ModelSerializer):
    """Invitation Serializer"""

    created_by = PartialUserSerializer(read_only=True)
    fixed_data = JSONDictField(required=False)
    flow_obj = FlowSerializer(read_only=True, required=False, source="flow")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["created_by"] = PrimaryKeyRelatedField(
                queryset=User.objects.all(),
                required=False,
                allow_null=True,
                default=get_anonymous_user(),
            )

    class Meta:
        model = Invitation
        fields = [
            "pk",
            "name",
            "expires",
            "fixed_data",
            "created_by",
            "single_use",
            "flow",
            "flow_obj",
        ]


class InvitationSendEmailSerializer(Serializer):
    """Serializer for sending invitation emails"""

    email_addresses = ListField(required=True)
    cc_addresses = ListField(required=False)
    bcc_addresses = ListField(required=False)
    template = CharField(required=False, default="invitation")


class InvitationViewSet(UsedByMixin, ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    ordering = ["-expires"]
    search_fields = ["name", "created_by__username", "expires", "flow__slug"]
    filterset_fields = ["name", "created_by__username", "expires", "flow__slug"]

    def perform_create(self, serializer: InvitationSerializer):
        kwargs = {}
        if SERIALIZER_CONTEXT_BLUEPRINT not in serializer.context:
            kwargs["created_by"] = self.request.user
        serializer.save(**kwargs)

    @extend_schema(
        request=InvitationSendEmailSerializer,
        responses={204: None},
    )
    @action(
        detail=True,
        methods=["post"],
        serializer_class=InvitationSendEmailSerializer,
    )
    def send_email(self, request: Request, pk: str) -> Response:
        """Send invitation link via email to one or more addresses"""
        invitation = self.get_object()
        email_addresses = request.data.get("email_addresses", [])
        cc_addresses = request.data.get("cc_addresses", [])
        bcc_addresses = request.data.get("bcc_addresses", [])
        template = request.data.get("template", "email/invitation.html")

        if not email_addresses:
            return Response({"error": "No email addresses provided"}, status=400)

        # Build the invitation link
        http_request: HttpRequest = request._request
        protocol = "https" if http_request.is_secure() else "http"
        host = http_request.get_host()

        # Determine the flow slug
        flow_slug = invitation.flow.slug if invitation.flow else None
        if not flow_slug:
            return Response({"error": "Invitation has no associated flow"}, status=400)

        invitation_link = f"{protocol}://{host}/if/flow/{flow_slug}/?itoken={invitation.pk}"

        # Prepare template context
        context = {
            "url": invitation_link,
            "expires": invitation.expires,
            "host": host,
        }

        # Prepare email content
        subject = f"You have been invited to {host}"

        # Queue emails for sending using ak_send_email
        evaluator = BaseEvaluator()

        for email in email_addresses:
            try:
                evaluator.expr_send_email(
                    address=email,
                    subject=subject,
                    template=template,
                    context=context,
                    stage=None,
                    cc=cc_addresses if cc_addresses else None,
                    bcc=bcc_addresses if bcc_addresses else None,
                )
            except (SMTPException, ConnectionError, ValidationError, ValueError) as exc:
                LOGGER.warning("Failed to queue invitation email", email=email, exc=exc)
                return Response(
                    {"error": f"Failed to queue email for {email}: {str(exc)}"}, status=500
                )

        return Response(status=204)
