from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.models import OffboardingStatus, UserOffboarding


class UserOffboardingSerializer(EnterpriseRequiredMixin, ModelSerializer):
    user_obj = PartialUserSerializer(source="user", read_only=True)
    created_by_obj = PartialUserSerializer(source="created_by", read_only=True)

    class Meta:
        model = UserOffboarding
        fields = [
            "id",
            "user",
            "user_obj",
            "scheduled_for",
            "action",
            "revoke_sessions",
            "revoke_tokens",
            "status",
            "created_by_obj",
            "created_at",
            "executed_on",
        ]
        read_only_fields = [
            "id",
            "user_obj",
            "status",
            "created_by_obj",
            "created_at",
            "executed_on",
        ]

    def validate_scheduled_for(self, value):
        if value <= now():
            raise ValidationError(_("Offboarding must be scheduled in the future."))
        return value

    def validate_user(self, user: User) -> User:
        if user.type == UserTypes.INTERNAL_SERVICE_ACCOUNT:
            raise ValidationError(_("Internal service accounts cannot be offboarded."))
        request = self.context.get("request")
        if request is not None and user.pk == request.user.pk:
            raise ValidationError(_("You cannot offboard your own account."))
        return user

    def validate(self, attrs: dict) -> dict:
        attrs = super().validate(attrs)
        # Enforce a single pending offboarding per user (mirrors the DB constraint
        # but returns a friendly error instead of an IntegrityError).
        user = attrs.get("user", getattr(self.instance, "user", None))
        if user is not None:
            existing = UserOffboarding.objects.filter(user=user, status=OffboardingStatus.PENDING)
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    {"user": _("This user already has a pending offboarding scheduled.")}
                )
        return attrs


class UserOffboardingViewSet(ModelViewSet):
    queryset = UserOffboarding.objects.select_related("user", "created_by").all()
    serializer_class = UserOffboardingSerializer
    search_fields = ["user__username"]
    ordering = ["scheduled_for"]
    ordering_fields = ["scheduled_for", "created_at", "status"]
    filterset_fields = ["user__uuid", "status", "action"]

    def perform_create(self, serializer: UserOffboardingSerializer) -> None:
        serializer.save(created_by=self.request.user)
