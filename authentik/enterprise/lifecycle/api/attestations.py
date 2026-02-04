from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.models import Attestation
from authentik.enterprise.lifecycle.utils import ReviewerUserSerializer


class AttestationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    reviewer = ReviewerUserSerializer(read_only=True)

    class Meta:
        model = Attestation
        fields = ["id", "review", "reviewer", "timestamp", "note"]
        read_only_fields = ["id", "timestamp", "reviewer"]

    def validate_review(self, review):
        user = self.context["request"].user
        if not review.user_can_attest(user):
            raise ValidationError(_("You are not allowed to attest on this review."))
        return review


class AttestationViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Attestation.objects.all()
    serializer_class = AttestationSerializer

    def perform_create(self, serializer: AttestationSerializer) -> None:
        attestation = serializer.save(reviewer=self.request.user)
        attestation.review.on_attestation(self.request)
