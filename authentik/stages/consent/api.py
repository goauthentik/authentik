"""ConsentStage API Views"""
from django_filters.rest_framework import DjangoFilterBackend
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
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
        fields = ["pk", "expires", "user", "application"]


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
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    ]
    search_fields = ["user__username"]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
