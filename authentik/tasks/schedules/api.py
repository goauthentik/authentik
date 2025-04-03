from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.rbac.decorators import permission_required
from authentik.tasks.schedules.models import Schedule


class ScheduleSerializer(ModelSerializer):
    description = SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            "id",
            "uid",
            "actor_name",
            "crontab",
            "paused",
            "next_run",
            "description",
        ]

    def get_description(self, instance: Schedule) -> str | None:
        if instance.rel_obj:
            for spec in instance.rel_obj.schedule_specs:
                if instance.uid == spec.get_uid():
                    return spec.description
        try:
            actor: Actor = get_broker().get_actor(instance.actor_name)
        except ActorNotFound:
            return "FIXME this shouldn't happen"
        return actor.fn.__doc__.strip()


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
        "uid",
    )
    ordering = ("next_run", "uid")

    @permission_required("authentik_tasks_schedules.send_schedule")
    @extend_schema(request=OpenApiTypes.NONE)
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def send(self, request: Request, pk=None) -> Response:
        """Trigger this schedule now"""
        schedule: Schedule = self.get_object()
        schedule.send()
        return Response({})
