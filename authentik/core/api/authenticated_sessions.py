"""AuthenticatedSessions API Viewset"""
from guardian.utils import get_anonymous_user
from rest_framework import mixins
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet

from authentik.core.models import AuthenticatedSession


class AuthenticatedSessionSerializer(ModelSerializer):
    """AuthenticatedSession Serializer"""

    class Meta:

        model = AuthenticatedSession
        fields = [
            "uuid",
            "user",
            "last_ip",
            "last_user_agent",
            "last_used",
            "expires",
        ]


class AuthenticatedSessionViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """AuthenticatedSession Viewset"""

    queryset = AuthenticatedSession.objects.all()
    serializer_class = AuthenticatedSessionSerializer
    search_fields = ["user__username", "last_ip", "last_user_agent"]
    filterset_fields = ["user__username", "last_ip", "last_user_agent"]
    ordering = ["user__username"]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)
