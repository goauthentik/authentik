from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import CreateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.enterprise.reviews.api.utils import GenericForeignKeySerializer, parse_content_type
from authentik.enterprise.reviews.models import Review


class ReviewSerializer(EnterpriseRequiredMixin, ModelSerializer):
    object = GenericForeignKeySerializer()

    class Meta:
        model = Review
        fields = ["id", "object", "state", "opened_on"]
        read_only_fields = ["opened_on", "target_verbose"]


class ReviewViewSet(EnterpriseRequiredMixin, CreateModelMixin, GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path=r"latest/(?P<content_type>[^/]+)/(?P<object_id>[^/]+)",
    )
    def latest_review(self, request: Request, content_type: str, object_id: str) -> Response:
        ct = parse_content_type(content_type)
        obj = get_object_or_404(
            self.get_queryset(),
            content_type__app_label=ct["app_label"],
            content_type__model=ct["model"],
            object_id=object_id,
        )
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
