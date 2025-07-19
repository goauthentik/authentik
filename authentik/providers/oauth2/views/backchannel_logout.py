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

from authentik.core.models import Application, AuthenticatedSession, User
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider, RefreshToken

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
                        # Revoke all tokens associated with this session
                        AccessToken.objects.filter(session=session).update(revoked=True)
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
                    user = self._find_user_by_sub(sub)
                    if user:
                        LOGGER.info("Received logout request for user", sub=sub, user=user.username)
                        # Terminate all sessions for this user with this provider
                        self._terminate_user_sessions(user)
                    else:
                        LOGGER.warning("User not found for sub claim", sub=sub)
                        return {"success": False, "error_description": "User not found"}
                except Exception as exc:
                    LOGGER.warning("Failed to process user logout", sub=sub, exc=exc)
                    return {"success": False, "error_description": "Failed to process user logout"}

            return {"success": True}
        except Exception as exc:
            LOGGER.warning("Error processing logout token", exc=exc)
            return {"success": False, "error_description": "Error processing logout token"}

    def _find_user_by_sub(self, sub: str) -> User | None:
        """Find user based on sub claim according to provider's sub_mode configuration"""
        from authentik.providers.oauth2.constants import SubModes

        try:
            if self.provider.sub_mode == SubModes.HASHED_USER_ID:
                # sub is the user's uid (hashed user ID)
                # Since uid is a computed property, we need to find the user by iterating
                # This is not efficient but necessary for the hashed mode
                for user in User.objects.all():
                    if user.uid == sub:
                        return user
                return None
            elif self.provider.sub_mode == SubModes.USER_ID:
                # sub is the user's primary key
                return User.objects.filter(pk=int(sub)).first()
            elif self.provider.sub_mode == SubModes.USER_UUID:
                # sub is the user's UUID
                return User.objects.filter(uuid=sub).first()
            elif self.provider.sub_mode == SubModes.USER_EMAIL:
                # sub is the user's email
                return User.objects.filter(email=sub).first()
            elif self.provider.sub_mode == SubModes.USER_USERNAME:
                # sub is the user's username
                return User.objects.filter(username=sub).first()
            elif self.provider.sub_mode == SubModes.USER_UPN:
                # sub is the user's UPN attribute or fallback to uid
                user = User.objects.filter(attributes__upn=sub).first()
                if not user:
                    # Fallback to uid if UPN not found (uid is a computed property)
                    for candidate_user in User.objects.all():
                        if candidate_user.uid == sub:
                            return candidate_user
                return user
            else:
                LOGGER.warning(
                    "Invalid sub_mode configuration",
                    provider=self.provider.name,
                    sub_mode=self.provider.sub_mode,
                )
                return None
        except (ValueError, TypeError) as exc:
            LOGGER.warning("Error parsing sub claim", sub=sub, exc=exc)
            return None

    def _terminate_user_sessions(self, user: User) -> None:
        """Terminate all sessions for the user that have tokens from this provider"""
        # Find all sessions that have tokens from this provider for this user
        session_ids = set()

        # Get sessions from access tokens
        access_tokens = AccessToken.objects.filter(user=user, provider=self.provider)
        for token in access_tokens:
            if token.session:
                session_ids.add(token.session.pk)

        # Get sessions from refresh tokens
        refresh_tokens = RefreshToken.objects.filter(user=user, provider=self.provider)
        for token in refresh_tokens:
            if token.session:
                session_ids.add(token.session.pk)

        # Revoke all tokens for this user and provider
        AccessToken.objects.filter(user=user, provider=self.provider).update(revoked=True)
        RefreshToken.objects.filter(user=user, provider=self.provider).update(revoked=True)

        # Terminate the sessions
        for session_id in session_ids:
            try:
                session = AuthenticatedSession.objects.get(pk=session_id)
                # Store session key before deleting the session
                session_key = session.session.session_key if hasattr(session, "session") else None
                username = user.username
                provider_name = self.provider.name

                # Delete the session
                session.delete()

                LOGGER.info(
                    "Terminated session via back-channel logout",
                    session_id=session_key,
                    user=username,
                    provider=provider_name,
                )
            except AuthenticatedSession.DoesNotExist:
                LOGGER.debug("Session already terminated", session_id=session_id)
