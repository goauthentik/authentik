"""Identification Stage API Views"""
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.identification.models import IdentificationStage


class IdentificationStageSerializer(StageSerializer):
    """IdentificationStage Serializer"""

    def validate(self, attrs: dict) -> dict:
        # Check that at least 1 source is selected when no user fields are selected.
        sources = attrs.get("sources", [])
        user_fields = attrs.get("user_fields", [])
        if len(user_fields) < 1 and len(sources) < 1:
            raise ValidationError(
                _("When no user fields are selected, at least one source must be selected")
            )
        return super().validate(attrs)

    class Meta:
        model = IdentificationStage
        fields = StageSerializer.Meta.fields + [
            "user_fields",
            "password_stage",
            "case_insensitive_matching",
            "show_matched_user",
            "enrollment_flow",
            "recovery_flow",
            "passwordless_flow",
            "sources",
            "show_source_labels",
        ]


class IdentificationStageViewSet(UsedByMixin, ModelViewSet):
    """IdentificationStage Viewset"""

    queryset = IdentificationStage.objects.all()
    serializer_class = IdentificationStageSerializer
    filterset_fields = [
        "name",
        "password_stage",
        "case_insensitive_matching",
        "show_matched_user",
        "enrollment_flow",
        "recovery_flow",
        "passwordless_flow",
        "show_source_labels",
    ]
    search_fields = ["name"]
    ordering = ["name"]
