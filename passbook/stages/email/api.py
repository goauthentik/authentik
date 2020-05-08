"""EmailStage API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.stages.email.models import EmailStage


class EmailStageSerializer(ModelSerializer):
    """EmailStage Serializer"""

    class Meta:

        model = EmailStage
        fields = [
            "pk",
            "name",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
            "ssl_keyfile",
            "ssl_certfile",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class EmailStageViewSet(ModelViewSet):
    """EmailStage Viewset"""

    queryset = EmailStage.objects.all()
    serializer_class = EmailStageSerializer
