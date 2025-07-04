"""OAuth2 Provider Back-Channel Logout Views"""

from typing import Any

import jwt
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt.exceptions import InvalidTokenError
from structlog.stdlib import get_logger

from authentik.core.models import Application, AuthenticatedSession
from authentik.providers.oauth2.models import OAuth2Provider, RefreshToken

LOGGER = get_logger()


@method_decorator(csrf_exempt, name="dispatch")
class BackChannelLogoutView(View):
    """Handle OpenID Connect Back-Channel Logout requests

    As per https://openid.net/specs/openid-connect-backchannel-1_0.html
    """

    provider: OAuth2Provider

    def post(self, request: HttpRequest, application_slug: str) -> HttpResponse:
        """Handle Back-Channel Logout Request"""
        try:
            # Get the provider based on the application slug
            application = get_object_or_404(Application, slug=application_slug)
            self.provider = application.get_provider()
            if not isinstance(self.provider, OAuth2Provider):
                return JsonResponse(
                    {"error": "invalid_request", "error_description": "Invalid provider type"},
                    status=400,
                )

            # Parse and validate the logout token
            logout_token = request.POST.get("logout_token")
            if not logout_token:
                return JsonResponse(
                    {"error": "invalid_request", "error_description": "Missing logout_token"},
                    status=400,
                )

            # Process the logout token and perform session termination
            result = self.process_logout_token(request, logout_token)
            if not result["success"]:
                return JsonResponse(
                    {"error": "invalid_request", "error_description": result["error_description"]},
                    status=400,
                )

            # Return successful response
            return HttpResponse(status=200)
        except Exception as exc:
            LOGGER.warning("Error processing back-channel logout", exc=exc)
            return JsonResponse(
                {"error": "server_error", "error_description": "Internal server error"},
                status=500,
            )

    def process_logout_token(self, request: HttpRequest, logout_token: str) -> dict[str, Any]:
        """Process the logout token and terminate sessions"""
        try:
            # Decode and validate the logout token
            key, alg = self.provider.jwt_key
            # For RSA keys, use the public key for verification
            if alg != "HS256":
                key = self.provider.signing_key.public_key
            try:
                token_data = jwt.decode(
                    logout_token,
                    key,
                    algorithms=[alg],
                    audience=self.provider.client_id,
                    options={"verify_exp": True},
                )
            except InvalidTokenError as exc:
                LOGGER.warning("Invalid logout token", exc=exc)
                return {"success": False, "error_description": "Invalid logout token"}

            # Validate required claims
            issuer = self.provider.get_issuer(request)
            if "iss" not in token_data or token_data["iss"] != issuer:
                return {"success": False, "error_description": "Invalid issuer"}

            if "sub" not in token_data and "sid" not in token_data:
                return {"success": False, "error_description": "Missing sub or sid claim"}

            # Check for events claim
            backchannel_event = "http://schemas.openid.net/event/backchannel-logout"
            if "events" not in token_data or backchannel_event not in token_data["events"]:
                return {"success": False, "error_description": "Invalid events claim"}

            # Process logout based on sid (session ID) if present
            if "sid" in token_data:
                session_id = token_data["sid"]
                try:
                    # Find and terminate the session
                    session = AuthenticatedSession.objects.filter(
                        session__session_key=session_id
                    ).first()
                    if session:
                        # Revoke all refresh tokens associated with this session
                        RefreshToken.objects.filter(session=session).update(revoked=True)
                        # End the session
                        session.delete()
                        LOGGER.info(
                            "Terminated session via back-channel logout", session_id=session_id
                        )
                except Exception as exc:
                    LOGGER.warning("Failed to terminate session", session_id=session_id, exc=exc)
                    return {"success": False, "error_description": "Failed to terminate session"}

            # Process logout based on sub (user identifier) if present
            if "sub" in token_data:
                sub = token_data["sub"]
                try:
                    # Find the user based on the sub claim
                    # This depends on sub_mode configuration
                    LOGGER.info("Received logout request for user", sub=sub)
                    # TODO: Implement user session termination logic here based on sub_mode
                except Exception as exc:
                    LOGGER.warning("Failed to process user logout", sub=sub, exc=exc)
                    return {"success": False, "error_description": "Failed to process user logout"}

            return {"success": True}
        except Exception as exc:
            LOGGER.warning("Error processing logout token", exc=exc)
            return {"success": False, "error_description": "Error processing logout token"}
