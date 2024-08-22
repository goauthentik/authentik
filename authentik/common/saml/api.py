from rest_framework.fields import CharField

from authentik.core.api.utils import PassiveSerializer


class SAMLMetadataSerializer(PassiveSerializer):
    """SAML Provider Metadata serializer"""

    metadata = CharField(read_only=True)
    download_url = CharField(read_only=True, required=False)
