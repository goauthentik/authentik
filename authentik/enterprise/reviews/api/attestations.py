from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reviews.models import Attestation


class AttestationSerializer(EnterpriseRequiredMixin, ModelSerializer):
    class Meta:
        model = Attestation
        fields = ["id", "review", "reviewer", "timestamp", "note"]
        read_only_fields = ["id", "timestamp"]
