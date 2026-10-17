"""Invitation Stage API Views"""

from urllib.parse import urlencode

from django.urls import reverse
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
from authentik.lib.utils.email import normalize_addresses
from authentik.stages.email.models import EmailTemplate
from authentik.stages.email.tasks import send_mails
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.stages.invitation.models import Invitation, InvitationStage
from authentik.stages.invitation.stage import QS_INVITATION_TOKEN_KEY

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

    email_addresses = ListField(child=CharField(), required=True)
    cc_addresses = ListField(child=CharField(), required=False)
    bcc_addresses = ListField(child=CharField(), required=False)
    template = PrimaryKeyRelatedField(queryset=EmailTemplate.objects.all())


class InvitationViewSet(UsedByMixin, ModelViewSet):
    """Invitation Viewset"""

    queryset = Invitation.objects.including_expired().all()
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
        serializer = InvitationSendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_addresses = serializer.validated_data["email_addresses"]
        cc_addresses = serializer.validated_data.get("cc_addresses")
        bcc_addresses = serializer.validated_data.get("bcc_addresses")
        template: EmailTemplate = serializer.validated_data["template"]

        if not email_addresses:
            return Response({"error": "No email addresses provided"}, status=400)
        # Determine the flow slug
        flow_slug = invitation.flow.slug if invitation.flow else None
        if not flow_slug:
            return Response({"error": "Invitation has no associated flow"}, status=400)

        # Build the invitation link
        invitation_link = request._request.build_absolute_uri(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow_slug})
            + "?"
            + urlencode({QS_INVITATION_TOKEN_KEY: invitation.pk})
        )

        # Prepare template context
        host = request.get_host()
        context = {
            "url": invitation_link,
            "expires": invitation.expires,
            "host": host,
        }

        # Prepare email content
        subject = f"You have been invited to {host}"

        # Send emails
        messages = [
            TemplateEmailMessage(
                subject=subject,
                to=normalize_addresses(email),
                cc=normalize_addresses(cc_addresses) if cc_addresses else None,
                bcc=normalize_addresses(bcc_addresses) if bcc_addresses else None,
                template=template,
                template_context=context,
            )
            for email in email_addresses
        ]
        send_mails(None, *messages)

        return Response(status=204)
