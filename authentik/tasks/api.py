from django_filters.filters import BooleanFilter, MultipleChoiceFilter
from django_filters.filterset import FilterSet
from rest_framework.fields import ReadOnlyField
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.events.logs import LogEventSerializer
from authentik.tasks.models import Task, TaskStatus
from authentik.tenants.utils import get_current_tenant


class TaskSerializer(ModelSerializer):
    rel_obj_app_label = ReadOnlyField(source="rel_obj_content_type.app_label")
    rel_obj_model = ReadOnlyField(source="rel_obj_content_type.model")

    messages = LogEventSerializer(many=True, source="_messages")
    previous_messages = LogEventSerializer(many=True, source="_previous_messages")

    class Meta:
        model = Task
        fields = [
            "message_id",
            "queue_name",
            "actor_name",
            "state",
            "mtime",
            "rel_obj_app_label",
            "rel_obj_model",
            "rel_obj_id",
            "uid",
            "messages",
            "previous_messages",
            "aggregated_status",
        ]


class TaskFilter(FilterSet):
    rel_obj_id__isnull = BooleanFilter("rel_obj_id", "isnull")
    aggregated_status = MultipleChoiceFilter(
        choices=TaskStatus.choices,
        field_name="aggregated_status",
    )

    class Meta:
        model = Task
        fields = (
            "queue_name",
            "actor_name",
            "state",
            "rel_obj_content_type__app_label",
            "rel_obj_content_type__model",
            "rel_obj_id",
            "rel_obj_id__isnull",
            "aggregated_status",
        )


class TaskViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = Task.objects.none()
    serializer_class = TaskSerializer
    search_fields = (
        "message_id",
        "queue_name",
        "actor_name",
        "state",
        "rel_obj_content_type__app_label",
        "rel_obj_content_type__model",
        "rel_obj_id",
        "_uid",
        "aggregated_status",
    )
    filterset_class = TaskFilter
    ordering = ("-mtime",)

    def get_queryset(self):
        return Task.objects.select_related("rel_obj_content_type").filter(
            tenant=get_current_tenant()
        )
