"""RAC Connection override API"""

from authentik.core.api.utils import ModelSerializer
from authentik.providers.rac.models import RACConnectionOverride


class RACConnectionOverrideSerializer(ModelSerializer):
    """RACConnectionOverride Serializer"""

    class Meta:
        model = RACConnectionOverride
        fields = [
            "host",
            "protocol",
        ]
