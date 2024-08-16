from django.http import HttpResponse
from rest_framework.fields import CharField, ChoiceField, ListField
from rest_framework.request import Request
from structlog.stdlib import get_logger

from authentik.core.api.utils import PassiveSerializer
from authentik.enterprise.providers.ssf.models import DeliveryMethods, EventTypes
from authentik.enterprise.providers.ssf.views.base import SSFView

LOGGER = get_logger()


class StreamDeliverySerializer(PassiveSerializer):
    method = ChoiceField(choices=[(x.value, x.value) for x in DeliveryMethods])
    endpoint_url = CharField(allow_null=True)


class StreamSerializer(PassiveSerializer):
    delivery = StreamDeliverySerializer()
    events_requested = ListField(
        child=ChoiceField(choices=[(x.value, x.value) for x in EventTypes])
    )


class StreamView(SSFView):
    # def setup(self, request: HttpRequest, *args, **kwargs) -> None:
    #     self.application = get_object_or_404(Application, slug=self.kwargs["application_slug"])
    #     self.provider = get_object_or_404(SSFProvider, slug=self.kwargs["provider"])
    #     # TODO: Auth
    #     return super().setup(request, *args, **kwargs)

    def post(self, request: Request, *args, **kwargs) -> HttpResponse:
        payload = StreamSerializer(request.data)
        payload.is_valid(raise_exception=True)
