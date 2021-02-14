"""WebAuthnStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.stages.webauthn.models import WebAuthnStage


class WebAuthnStageSerializer(ModelSerializer):
    """WebAuthnStage Serializer"""

    class Meta:

        model = WebAuthnStage
        fields = ["pk", "name"]


class WebAuthnStageViewSet(ModelViewSet):
    """WebAuthnStage Viewset"""

    queryset = WebAuthnStage.objects.all()
    serializer_class = WebAuthnStageSerializer
