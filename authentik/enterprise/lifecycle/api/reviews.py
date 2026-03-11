from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.lifecycle.models import LifecycleIteration, Review
from authentik.enterprise.lifecycle.utils import ReviewerUserSerializer


class ReviewSerializer(EnterpriseRequiredMixin, ModelSerializer):
    reviewer = ReviewerUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ["id", "iteration", "reviewer", "timestamp", "note"]
        read_only_fields = ["id", "timestamp", "reviewer"]

    def validate_iteration(self, iteration: LifecycleIteration) -> LifecycleIteration:
        user = self.context["request"].user
        if not iteration.user_can_review(user):
            raise ValidationError(_("You are not allowed to submit a review for this object."))
        return iteration


class ReviewViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def perform_create(self, serializer: ReviewSerializer) -> None:
        review = serializer.save(reviewer=self.request.user)
        review.iteration.on_review(self.request)
