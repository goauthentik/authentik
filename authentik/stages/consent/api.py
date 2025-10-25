"""ConsentStage API Views"""

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.applications import ApplicationSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.flows.api.stages import StageSerializer
from authentik.stages.consent.models import ConsentStage, UserConsent


class ConsentStageSerializer(StageSerializer):
    """ConsentStage Serializer"""

    class Meta:
        model = ConsentStage
        fields = StageSerializer.Meta.fields + ["mode", "consent_expire_in"]


class ConsentStageViewSet(UsedByMixin, ModelViewSet):
    """ConsentStage Viewset"""

    queryset = ConsentStage.objects.all()
    serializer_class = ConsentStageSerializer
    filterset_fields = "__all__"
    ordering = ["name"]
    search_fields = ["name"]


class UserConsentSerializer(StageSerializer):
    """UserConsent Serializer"""

    user = UserSerializer()
    application = ApplicationSerializer()

    class Meta:
        model = UserConsent
        fields = ["pk", "expires", "expiring", "user", "application", "permissions"]


class UserConsentViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """UserConsent Viewset"""

    queryset = UserConsent.objects.all()
    serializer_class = UserConsentSerializer
    filterset_fields = ["user", "application"]
    ordering = ["application", "expires"]
    search_fields = ["user__username"]
    owner_field = "user"
