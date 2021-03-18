"""ConsentStage API Views"""
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.users import UserSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.consent.models import ConsentStage, UserConsent


class ConsentStageSerializer(StageSerializer):
    """ConsentStage Serializer"""

    class Meta:

        model = ConsentStage
        fields = StageSerializer.Meta.fields + ["mode", "consent_expire_in"]


class ConsentStageViewSet(ModelViewSet):
    """ConsentStage Viewset"""

    queryset = ConsentStage.objects.all()
    serializer_class = ConsentStageSerializer


class UserConsentSerializer(StageSerializer):
    """UserConsent Serializer"""

    user = UserSerializer()
    application = ApplicationSerializer()

    class Meta:

        model = UserConsent
        fields = ["pk", "expires", "user", "application"]


class UserConsentViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """UserConsent Viewset"""

    queryset = UserConsent.objects.all()
    serializer_class = UserConsentSerializer
    filterset_fields = ["user", "application"]
    ordering = ["application", "expires"]

    def get_queryset(self):
        if not self.request:
            return super().get_queryset()
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
