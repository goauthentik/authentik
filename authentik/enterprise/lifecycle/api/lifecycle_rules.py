from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import SlugRelatedField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.core.models import User
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.models import LifecycleRule
from authentik.enterprise.lifecycle.utils import (
    ContentTypeField,
    ReviewerGroupSerializer,
    ReviewerUserSerializer,
)
from authentik.lib.utils.time import timedelta_from_string


class LifecycleRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):
    content_type = ContentTypeField()
    target_verbose = SerializerMethodField()
    reviewer_groups_obj = ReviewerGroupSerializer(
        many=True, read_only=True, source="reviewer_groups"
    )
    reviewers = SlugRelatedField(slug_field="uuid", many=True, queryset=User.objects.all())
    reviewers_obj = ReviewerUserSerializer(many=True, read_only=True, source="reviewers")

    class Meta:
        model = LifecycleRule
        fields = [
            "id",
            "name",
            "content_type",
            "object_id",
            "interval",
            "grace_period",
            "reviewer_groups",
            "reviewer_groups_obj",
            "min_reviewers",
            "min_reviewers_is_per_group",
            "reviewers",
            "reviewers_obj",
            "notification_transports",
            "target_verbose",
        ]
        read_only_fields = ["id", "reviewers_obj", "reviewer_groups_obj", "target_verbose"]

    def get_target_verbose(self, rule: LifecycleRule) -> str:
        if rule.object_id is None:
            return rule.content_type.model_class()._meta.verbose_name_plural
        else:
            return f"{rule.content_type.model_class()._meta.verbose_name}: {rule.object}"

    def validate_object_id(self, value: str) -> str | None:
        if value == "":
            return None
        return value

    def validate(self, attrs: dict) -> dict:
        if (
            attrs.get("object_id") is not None
            and not attrs["content_type"]
            .get_all_objects_for_this_type(pk=attrs["object_id"])
            .exists()
        ):
            raise ValidationError({"object_id": _("Object does not exist")})
        if "reviewer_groups" in attrs or "reviewers" in attrs:
            reviewer_groups = attrs.get(
                "reviewer_groups", self.instance.reviewer_groups.all() if self.instance else []
            )
            reviewers = attrs.get(
                "reviewers", self.instance.reviewers.all() if self.instance else []
            )
            if len(reviewer_groups) == 0 and len(reviewers) == 0:
                raise ValidationError(_("Either a reviewer group or a reviewer must be set."))
        if "grace_period" in attrs or "interval" in attrs:
            grace_period = attrs.get("grace_period", getattr(self.instance, "grace_period", None))
            interval = attrs.get("interval", getattr(self.instance, "interval", None))
            if (
                grace_period is not None
                and interval is not None
                and (timedelta_from_string(grace_period) > timedelta_from_string(interval))
            ):
                raise ValidationError(
                    {"grace_period": _("Grace period must be shorter than the interval.")}
                )
        if "content_type" in attrs or "object_id" in attrs:
            content_type = attrs.get("content_type", getattr(self.instance, "content_type", None))
            object_id = attrs.get("object_id", getattr(self.instance, "object_id", None))
            if content_type is not None and object_id is None:
                existing = LifecycleRule.objects.filter(
                    content_type=content_type, object_id__isnull=True
                )
                if self.instance:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise ValidationError(
                        {
                            "content_type": _(
                                "Only one type-wide rule for each object type is allowed."
                            )
                        }
                    )
        return attrs


class LifecycleRuleViewSet(ModelViewSet):
    queryset = LifecycleRule.objects.all()
    serializer_class = LifecycleRuleSerializer
    search_fields = ["content_type__model", "reviewer_groups__name", "reviewers__username"]
    ordering = ["name"]
    ordering_fields = ["name", "content_type__model"]
    filterset_fields = ["content_type__model"]
