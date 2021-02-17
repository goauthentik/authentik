"""EmailStage API Views"""
from rest_framework.viewsets import ModelViewSet

from authentik.flows.api import StageSerializer
from authentik.stages.email.models import EmailStage, get_template_choices


class EmailStageSerializer(StageSerializer):
    """EmailStage Serializer"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].choices = get_template_choices()

    class Meta:

        model = EmailStage
        fields = StageSerializer.Meta.fields + [
            "use_global_settings",
            "host",
            "port",
            "username",
            "password",
            "use_tls",
            "use_ssl",
            "timeout",
            "from_address",
            "token_expiry",
            "subject",
            "template",
        ]
        extra_kwargs = {"password": {"write_only": True}}


class EmailStageViewSet(ModelViewSet):
    """EmailStage Viewset"""

    queryset = EmailStage.objects.all()
    serializer_class = EmailStageSerializer
