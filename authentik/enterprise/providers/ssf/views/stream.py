from uuid import uuid4

from django.http import Http404, HttpRequest
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import CharField, ChoiceField, ListField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.enterprise.providers.ssf.models import (
    DeliveryMethods,
    EventTypes,
    SSFProvider,
    Stream,
    StreamStatus,
)
from authentik.enterprise.providers.ssf.tasks import send_ssf_events
from authentik.enterprise.providers.ssf.views.base import SSFStreamView

LOGGER = get_logger()


class StreamDeliverySerializer(PassiveSerializer):
    method = ChoiceField(choices=[(x.value, x.value) for x in DeliveryMethods])
    endpoint_url = CharField(required=False)
    authorization_header = CharField(required=False)

    def validate_method(self, method: DeliveryMethods):
        """Currently only push is supported"""
        if method == DeliveryMethods.RISC_POLL:
            raise ValidationError("Polling for SSF events is not currently supported.")
        return method

    def validate(self, attrs: dict) -> dict:
        if attrs.get("method") in [DeliveryMethods.RISC_PUSH, DeliveryMethods.RFC_PUSH]:
            if not attrs.get("endpoint_url"):
                raise ValidationError("Endpoint URL is required when using push.")
        return attrs


class StreamSerializer(ModelSerializer):
    delivery = StreamDeliverySerializer()
    events_requested = ListField(
        child=ChoiceField(choices=[(x.value, x.value) for x in EventTypes])
    )
    format = CharField(default="iss_sub")
    aud = ListField(child=CharField(), allow_empty=True, default=list)

    def create(self, validated_data):
        provider: SSFProvider = validated_data["provider"]
        request: HttpRequest = self.context["request"]
        iss = request.build_absolute_uri(
            reverse(
                "authentik_providers_ssf:configuration",
                kwargs={
                    "application_slug": provider.backchannel_application.slug,
                },
            )
        )
        # Ensure that streams always get SET verification events sent to them
        validated_data["events_requested"].append(EventTypes.SET_VERIFICATION)
        stream_id = uuid4()
        default_aud = f"goauthentik.io/providers/ssf/{str(stream_id)}"
        return super().create(
            {
                "delivery_method": validated_data["delivery"]["method"],
                "endpoint_url": validated_data["delivery"].get("endpoint_url"),
                "authorization_header": validated_data["delivery"].get("authorization_header"),
                "format": validated_data["format"],
                "provider": validated_data["provider"],
                "events_requested": validated_data["events_requested"],
                "aud": validated_data["aud"] or [default_aud],
                "iss": iss,
                "pk": stream_id,
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
        return [
            EventTypes.CAEP_SESSION_REVOKED,
            EventTypes.CAEP_CREDENTIAL_CHANGE,
            EventTypes.SET_VERIFICATION,
        ]


class StreamView(SSFStreamView):

    def get(self, request: Request, *args, **kwargs):
        stream = self.get_object()
        return Response(
            StreamResponseSerializer(instance=stream, context={"request": request}).data
        )

    @validate(StreamSerializer)
    def post(self, request: Request, *args, body: StreamSerializer, **kwargs) -> Response:
        if not request.user.has_perm("authentik_providers_ssf.add_stream", self.provider):
            raise PermissionDenied(
                "User does not have permission to create stream for this provider."
            )
        instance: Stream = body.save(provider=self.provider)

        LOGGER.info("Sending verification event", stream=instance)
        send_ssf_events(
            EventTypes.SET_VERIFICATION,
            {},
            stream_filter={"pk": instance.uuid},
            request=request,
            sub_id={"format": "opaque", "id": str(instance.uuid)},
        )
        response = StreamResponseSerializer(instance=instance, context={"request": request}).data
        return Response(response, status=201)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        stream = self.get_object()
        serializer = StreamSerializer(stream, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = StreamResponseSerializer(
            instance=serializer.instance, context={"request": request}
        ).data
        return Response(response, status=200)

    def put(self, request: Request, *args, **kwargs) -> Response:
        stream = self.get_object()
        serializer = StreamSerializer(stream, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = StreamResponseSerializer(
            instance=serializer.instance, context={"request": request}
        ).data
        return Response(response, status=200)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        stream = self.get_object()
        if stream.status == StreamStatus.DISABLED_DELETED:
            raise Http404
        stream.status = StreamStatus.DISABLED_DELETED
        stream.save()
        return Response(status=204)


class StreamVerifyView(SSFStreamView):

    def post(self, request: Request, *args, **kwargs):
        stream = self.get_object()
        state = request.data.get("state", None)
        send_ssf_events(
            EventTypes.SET_VERIFICATION,
            {
                "state": state,
            },
            stream_filter={"pk": stream.uuid},
            request=request,
            sub_id={"format": "opaque", "id": str(stream.uuid)},
        )
        return Response(status=204)


class StreamStatusView(SSFStreamView):

    class StreamStatusSerializer(PassiveSerializer):
        stream_id = CharField()
        status = ChoiceField(choices=StreamStatus.choices)

    def get(self, request: Request, *args, **kwargs):
        stream = self.get_object()
        return Response(
            {
                "stream_id": str(stream.pk),
                "status": str(stream.status),
            }
        )

    def post(self, request: Request, *args, **kwargs):
        stream = self.get_object()
        serializer = self.StreamStatusSerializer(stream, data=request.data)
        serializer.is_valid(raise_exception=True)
        stream.status = serializer.validated_data["status"]
        stream.save()
        return Response(
            {
                "stream_id": str(stream.pk),
                "status": str(stream.status),
            }
        )
