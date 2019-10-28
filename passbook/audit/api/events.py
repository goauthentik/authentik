from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from passbook.audit.models import Event


class EventSerializer(ModelSerializer):

    class Meta:

        model = Event
        fields = ['pk', 'user', 'action', 'date', 'app', 'context', 'request_ip', 'created', ]


class EventViewSet(ReadOnlyModelViewSet):

    queryset = Event.objects.all()
    serializer_class = EventSerializer
