"""Agent token-to-session exchange view"""

from django.contrib.auth import login
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from authentik.core.models import (
    USER_ATTRIBUTE_AGENT_OWNER_PK,
    AuthenticatedSession,
    Token,
    TokenIntents,
)
from authentik.stages.password import BACKEND_INBUILT


class NoAuthentication(BaseAuthentication):
    """Explicitly skip DRF authentication; the view authenticates via the request body."""

    def authenticate(self, request):
        return None


class AgentSessionView(APIView):
    """Exchange an agent's API token for an authenticated session."""

    authentication_classes = [NoAuthentication]
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        key = request.data.get("key")
        if not key:
            return Response({"detail": "Key is required."}, status=400)

        token = (
            Token.objects.filter(key=key, intent=TokenIntents.INTENT_API)
            .select_related("user")
            .first()
        )
        if not token:
            return Response({"detail": "Invalid token."}, status=400)
        if token.is_expired:
            return Response({"detail": "Token has expired."}, status=403)
        if not token.user.attributes.get(USER_ATTRIBUTE_AGENT_OWNER_PK):
            return Response({"detail": "Token does not belong to an agent user."}, status=400)
        if not token.user.is_active:
            return Response({"detail": "Agent user is inactive."}, status=403)

        login(request._request, token.user, backend=BACKEND_INBUILT)
        session = AuthenticatedSession.from_request(request._request, token.user)
        if session:
            session.save()
        return Response(status=204)
