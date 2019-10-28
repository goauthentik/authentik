from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.core.models import Invitation


class InvitationSerializer(ModelSerializer):

    class Meta:

        model = Invitation
        fields = ['pk', 'expires', 'fixed_username', 'fixed_email', 'needs_confirmation']


class InvitationViewSet(ModelViewSet):

    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
