from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import  GenericViewSet
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.utils import ReviewerUserSerializer
from authentik.enterprise.lifecycle.models import Attestation


class AttestationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    reviewer = ReviewerUserSerializer(read_only=True)

    class Meta:
        model = Attestation
        fields = ["id", "review", "reviewer", "timestamp", "note"]
        read_only_fields = ["id", "timestamp", "reviewer"]


class AttestationViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Attestation.objects.all()
    serializer_class = AttestationSerializer

    def perform_create(self, serializer: AttestationSerializer) -> None:
        attestation = serializer.save(reviewer=self.request.user)
        attestation.review.on_attestation(self.request)
