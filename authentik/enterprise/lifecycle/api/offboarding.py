from django.db import IntegrityError, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import PartialUserSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import User, UserTypes
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.models import OffboardingStatus, UserOffboarding

DUPLICATE_PENDING_ERROR = _("This user already has a pending offboarding scheduled.")


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
                raise ValidationError({"user": DUPLICATE_PENDING_ERROR})
        return attrs


class UserOffboardingViewSet(ModelViewSet):
    queryset = UserOffboarding.objects.select_related("user", "created_by").all()
    serializer_class = UserOffboardingSerializer
    search_fields = ["user__username"]
    ordering = ["scheduled_for"]
    ordering_fields = ["scheduled_for", "created_at", "status"]
    filterset_fields = ["user__uuid", "status", "action"]
    # Offboarding records are immutable: they can be scheduled (POST), cancelled
    # (DELETE → soft-cancel), and read — but never edited. PUT/PATCH would let a
    # terminal audit row's action/schedule/user be rewritten after the fact.
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer: UserOffboardingSerializer) -> None:
        # Two concurrent requests can both pass validate()'s duplicate check and
        # race to insert; the unique constraint rejects the loser. Catch it behind
        # a savepoint and return the same 400 instead of a 500.
        try:
            with transaction.atomic():
                serializer.save(created_by=self.request.user)
        except IntegrityError:
            raise ValidationError({"user": DUPLICATE_PENDING_ERROR}) from None

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Cancel a pending offboarding instead of deleting the record.

        The row is retained (as `CANCELED`) so the offboarding stays visible in
        the audit history; deletion would erase who scheduled and cancelled it.
        """
        offboarding: UserOffboarding = self.get_object()
        if not offboarding.cancel():
            raise ValidationError(_("Only a pending offboarding can be cancelled."))
        return Response(status=204)
