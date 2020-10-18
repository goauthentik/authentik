"""Tokens API Viewset"""
from uuid import UUID

from django.http.response import Http404
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.audit.models import Event, EventAction
from passbook.core.models import Token


class TokenSerializer(ModelSerializer):
    """Token Serializer"""

    class Meta:

        model = Token
        fields = ["pk", "identifier", "intent", "user", "description"]


class TokenViewSet(ModelViewSet):
    """Token Viewset"""

    lookup_field = "identifier"
    queryset = Token.filter_not_expired()
    serializer_class = TokenSerializer

    @action(detail=True)
    # pylint: disable=invalid-name
    def view_key(self, request: Request, pk: UUID) -> Response:
        """Return token key and log access"""
        tokens = Token.filter_not_expired(pk=pk)
        if not tokens.exists():
            raise Http404
        token = tokens.first()
        Event.new(EventAction.TOKEN_VIEW, token=token).from_http(request)
        return Response({"key": token.key})
