from django.urls import reverse
from rest_framework.fields import CharField, ChoiceField, ListField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from structlog.stdlib import get_logger

from authentik.core.api.utils import PassiveSerializer
from authentik.enterprise.providers.ssf.models import DeliveryMethods, EventTypes, Stream
from authentik.enterprise.providers.ssf.tasks import send_ssf_event
from authentik.enterprise.providers.ssf.views.base import SSFView

LOGGER = get_logger()


class StreamDeliverySerializer(PassiveSerializer):
    method = ChoiceField(choices=[(x.value, x.value) for x in DeliveryMethods])
    endpoint_url = CharField(allow_null=True)


class StreamSerializer(ModelSerializer):
    delivery = StreamDeliverySerializer()
    events_requested = ListField(
        child=ChoiceField(choices=[(x.value, x.value) for x in EventTypes])
    )
    format = CharField()
    aud = ListField(child=CharField())

    def create(self, validated_data):
        iss = self.context["request"].build_absolute_uri(
            reverse(
                "authentik_providers_ssf:configuration",
                kwargs={
                    "application_slug": validated_data["provider"].application.slug,
                    "provider": validated_data["provider"].pk,
                },
            )
        )
        return super().create(
            {
                "delivery_method": validated_data["delivery"]["method"],
                "endpoint_url": validated_data["delivery"].get("endpoint_url"),
                "format": validated_data["format"],
                "provider": validated_data["provider"],
                "events_requested": validated_data["events_requested"],
                "aud": validated_data["aud"],
                "iss": iss,
            }
        )

    class Meta:
        model = Stream
        fields = [
            "delivery",
            "events_requested",
            "format",
            "aud",
        ]


class StreamResponseSerializer(PassiveSerializer):
    stream_id = CharField(source="pk")
    iss = CharField()
    aud = ListField(child=CharField())
    delivery = SerializerMethodField()
    format = CharField()

    events_requested = ListField(child=CharField())
    events_supported = SerializerMethodField()
    events_delivered = ListField(child=CharField(), source="events_requested")

    def get_delivery(self, instance: Stream) -> StreamDeliverySerializer:
        return {
            "method": instance.delivery_method,
            "endpoint_url": instance.endpoint_url,
        }

    def get_events_supported(self, instance: Stream) -> list[str]:
        return [x.value for x in EventTypes]


class StreamView(SSFView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        stream = StreamSerializer(data=request.data, context={"request": request})
        stream.is_valid(raise_exception=True)
        instance: Stream = stream.save(provider=self.provider)
        send_ssf_event(
            EventTypes.SET_VERIFICATION,
            {
                "state": None,
            },
            stream_filter={"pk": instance.uuid},
            sub_id={"format": "opaque", "id": str(instance.uuid)},
        )
        response = StreamResponseSerializer(instance=instance, context={"request": request}).data
        return Response(response, status=201)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        streams = Stream.objects.filter(provider=self.provider)
        # Technically this parameter is required by the spec...
        if "stream_id" in request.query_params:
            streams = streams.filter(stream_id=request.query_params["stream_id"])
        streams.delete()
        return Response(status=204)
