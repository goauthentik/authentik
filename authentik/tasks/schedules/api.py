from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
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
    rel_obj_app_label = ReadOnlyField(source="rel_obj_content_type.app_label")
    rel_obj_model = ReadOnlyField(source="rel_obj_content_type.model")

    description = SerializerMethodField()

    class Meta:
        model = Schedule
        fields = (
            "id",
            "uid",
            "actor_name",
            "rel_obj_app_label",
            "rel_obj_model",
            "rel_obj_id",
            "crontab",
            "paused",
            "next_run",
            "description",
        )

    def get_description(self, instance: Schedule) -> str | None:
        if instance.rel_obj:
            for spec in instance.rel_obj.schedule_specs:
                if instance.uid == spec.get_uid():
                    return spec.description
        try:
            actor: Actor = get_broker().get_actor(instance.actor_name)
        except ActorNotFound:
            return "FIXME this shouldn't happen"
        if "description" not in actor.options:
            return "no doc"
        return actor.options["description"]


class ScheduleFilter(FilterSet):
    rel_obj_id__isnull = BooleanFilter("rel_obj_id", "isnull")

    class Meta:
        model = Schedule
        fields = (
            "actor_name",
            "rel_obj_content_type__app_label",
            "rel_obj_content_type__model",
            "rel_obj_id",
            "rel_obj_id__isnull",
            "paused",
        )


class ScheduleViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = Schedule.objects.select_related("rel_obj_content_type").all()
    serializer_class = ScheduleSerializer
    search_fields = (
        "id",
        "uid",
        "actor_name",
        "rel_obj_content_type__app_label",
        "rel_obj_content_type__model",
        "rel_obj_id",
        "description",
    )
    filterset_class = ScheduleFilter
    ordering = (
        "next_run",
        "uid",
    )

    @permission_required("authentik_tasks_schedules.send_schedule")
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Schedule sent successfully"),
            404: OpenApiResponse(description="Schedule not found"),
            500: OpenApiResponse(description="Failed to send schedule"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def send(self, request: Request, pk=None) -> Response:
        """Trigger this schedule now"""
        schedule: Schedule = self.get_object()
        schedule.send()
        return Response({})
