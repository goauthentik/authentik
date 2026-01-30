from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema_field
from rest_framework.exceptions import ValidationError
from rest_framework.fields import IntegerField, SerializerMethodField
from rest_framework.relations import SlugRelatedField
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.groups import RelatedGroupSerializer
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import User
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reviews.api.utils import ContentTypeField
from authentik.enterprise.reviews.models import LifecycleRule


class RelatedUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ["pk", "uuid", "username", "name"]


class LifecycleRuleSerializer(EnterpriseRequiredMixin, ModelSerializer):
    content_type = ContentTypeField()
    interval_months = IntegerField(min_value=1, max_value=24)
    grace_period_days = IntegerField(min_value=1, max_value=365)
    target_verbose = SerializerMethodField()
    reviewer_groups_obj = SerializerMethodField(allow_null=True)
    reviewers = SlugRelatedField(slug_field="uuid", many=True, queryset=User.objects.all())
    reviewers_obj = SerializerMethodField(allow_null=True)

    class Meta:
        model = LifecycleRule
        fields = [
            "id",
            "content_type",
            "object_id",
            "interval_months",
            "grace_period_days",
            "reviewer_groups",
            "reviewer_groups_obj",
            "min_reviewers",
            "reviewers",
            "reviewers_obj",
            "notification_transports",
            "target_verbose",
        ]
        read_only_fields = ["id", "reviewers_obj", "reviewer_groups_obj", "target_verbose"]

    def get_target_verbose(self, rule: LifecycleRule):
        if rule.object_id is None:
            return rule.content_type.model_class()._meta.verbose_name_plural
        else:
            return f"{rule.content_type.model_class()._meta.verbose_name}: {rule.object}"

    @extend_schema_field(RelatedGroupSerializer(many=True))
    def get_reviewer_groups_obj(
        self, instance: LifecycleRule
    ) -> list[RelatedGroupSerializer] | None:
        return RelatedGroupSerializer(instance.reviewer_groups, many=True).data

    @extend_schema_field(RelatedUserSerializer(many=True))
    def get_reviewers_obj(self, instance: LifecycleRule) -> list[RelatedUserSerializer] | None:
        return RelatedUserSerializer(instance.reviewers, many=True).data

    def validate_object_id(self, value: str) -> str | None:
        if value == "":
            return None
        return value

    def validate(self, attrs: dict):
        if (
            attrs["object_id"] is not None
            and not attrs["content_type"]
            .get_all_objects_for_this_type(pk=attrs["object_id"])
            .exists()
        ):
            raise ValidationError({"object_id": _("Object does not exist")})
        reviewer_groups = attrs.get("reviewer_groups", [])
        reviewers = attrs.get("reviewers", [])
        if len(reviewer_groups) == 0 and len(reviewers) == 0:
            raise ValidationError(_("Either a reviewer group or a reviewer must be set."))
        if len(reviewer_groups) > 0 and len(reviewers) > 0:
            raise ValidationError(_("Cannot set both reviewer groups and reviewers."))
        if attrs.get("grace_period_days") > 28 + (attrs.get("interval_months") - 1) * 30:
            raise ValidationError(
                {"grace_period": _("Grace period must be shorter than the interval.")}
            )
        return attrs


class LifecycleRuleViewSet(ModelViewSet):
    queryset = LifecycleRule.objects.all()
    serializer_class = LifecycleRuleSerializer
    search_fields = ["content_type__model", "reviewer_groups__name", "reviewers__username"]
