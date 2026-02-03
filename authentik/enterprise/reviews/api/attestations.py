from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import  GenericViewSet
from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reviews.utils import RelatedUserSerializer
from authentik.enterprise.reviews.models import Attestation


class AttestationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    reviewer = RelatedUserSerializer(read_only=True)

    class Meta:
        model = Attestation
        fields = ["id", "review", "reviewer", "timestamp", "note"]
        read_only_fields = ["id", "timestamp", "reviewer"]


class AttestationViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Attestation.objects.all()
    serializer_class = AttestationSerializer

    def perform_create(self, serializer: AttestationSerializer) -> None:
        serializer.save(reviewer=self.request.user)
