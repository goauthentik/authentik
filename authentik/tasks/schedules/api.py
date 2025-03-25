from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.tasks.schedules.models import Schedule


class ScheduleSerializer(ModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            "id",
            "name",
            "crontab",
            "next_run",
        ]


class ScheduleViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    search_fields = (
        "id",
        "name",
    )
    ordering = ("id",)
