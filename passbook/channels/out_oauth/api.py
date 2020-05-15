"""OAuth2Outlet API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.channels.out_oauth.models import OAuth2Outlet


class OAuth2OutletSerializer(ModelSerializer):
    """OAuth2Outlet Serializer"""

    class Meta:

        model = OAuth2Outlet
        fields = [
            "pk",
            "name",
            "redirect_uris",
            "client_type",
            "authorization_grant_type",
            "client_id",
            "client_secret",
        ]


class OAuth2OutletViewSet(ModelViewSet):
    """OAuth2Outlet Viewset"""

    queryset = OAuth2Outlet.objects.all()
    serializer_class = OAuth2OutletSerializer
