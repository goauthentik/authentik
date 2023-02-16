from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.interfaces.models import Interface


class InterfaceSerializer(ModelSerializer):
    class Meta:
        model = Interface
        fields = [
            "interface_uuid",
            "url_name",
            "type",
            "template",
        ]


class InterfaceViewSet(ModelViewSet):
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
