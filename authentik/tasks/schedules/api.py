from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.serializers import SerializerMethodField
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
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
