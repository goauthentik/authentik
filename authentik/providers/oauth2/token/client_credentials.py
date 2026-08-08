from base64 import b64decode
from datetime import datetime

from django.http import HttpRequest
from django.utils import timezone

from authentik.common.oauth.constants import (
    CLIENT_ASSERTION,
    CLIENT_ASSERTION_TYPE,
    CLIENT_ASSERTION_TYPE_JWT,
)
from authentik.core.models import (
    USER_ATTRIBUTE_GENERATED,
    USER_PATH_SYSTEM_PREFIX,
    USERNAME_MAX_LENGTH,
    Application,
    Token,
    TokenIntents,
    User,
    UserTypes,
)
from authentik.events.middleware import audit_ignore
from authentik.events.models import Event, EventAction
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.providers.oauth2.errors import TokenError
from authentik.providers.oauth2.token.base import TokenRequest
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS


class ClientCredentialsTokenRequest(TokenRequest):

    def parse(self, request: HttpRequest) -> None:
        super().parse(request)
        # client_credentials flow with client assertion
        if request.POST.get(CLIENT_ASSERTION_TYPE, "") != "":
            return self.post_init_client_credentials_jwt(request)
        # authentik-custom-ish client credentials flow
        if request.POST.get("username", "") != "":
            return self.post_init_client_credentials_creds(
                request, request.POST.get("username"), request.POST.get("password")
            )
        # Standard method which creates an automatic user
        if self.client_secret == self.provider.client_secret:
            return self.post_init_client_credentials_generated(request)
        # Standard workaround method which stores username:password
        # as client_secret
        try:
            user, _, password = b64decode(self.client_secret).decode("utf-8").partition(":")
            return self.post_init_client_credentials_creds(request, user, password)
        except ValueError:
            raise TokenError("invalid_grant") from None

    def post_init_client_credentials_creds(
        self, request: HttpRequest, username: str, password: str
    ):
        # Authenticate user based on credentials
        user = User.objects.filter(username=username, is_active=True).first()
        if not user:
            raise TokenError("invalid_grant")
        token: Token = Token.objects.filter(
            key=password, intent=TokenIntents.INTENT_APP_PASSWORD, user=user
        ).first()
        if not token or token.user.uid != user.uid:
            raise TokenError("invalid_grant")
        self.user = user
        # Authorize user access
        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            raise TokenError("invalid_grant")
        self.check_policy_access(app, request)

        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "token",
                PLAN_CONTEXT_METHOD_ARGS: {
                    "identifier": token.identifier,
                },
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=user)

    def post_init_client_credentials_jwt(self, request: HttpRequest):
        assertion_type = request.POST.get(CLIENT_ASSERTION_TYPE, "")
        if assertion_type != CLIENT_ASSERTION_TYPE_JWT:
            self.logger.warning("Invalid assertion type", assertion_type=assertion_type)
            raise TokenError("invalid_grant")

        client_secret = request.POST.get("client_secret", None)
        assertion = request.POST.get(CLIENT_ASSERTION, client_secret)
        if not assertion:
            self.logger.warning("Missing client assertion")
            raise TokenError("invalid_grant")

        provider = resolved_user = None

        token, source = self.validate_jwt_from_source(assertion)
        if not token:
            token, provider, resolved_user = self.validate_jwt_from_provider(assertion)

        if not token:
            self.logger.warning("No token could be verified")
            raise TokenError("invalid_grant")

        if "exp" in token:
            exp = datetime.fromtimestamp(token["exp"])
            # Non-timezone aware check since we assume `exp` is in UTC
            if datetime.now() >= exp:
                self.logger.info("JWT token expired")
                raise TokenError("invalid_grant")

        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            self.logger.info("client_credentials grant for provider without application")
            raise TokenError("invalid_grant")

        self.check_policy_access(app, request, oauth_jwt=token)
        if provider:
            self.user = resolved_user
        else:
            self.create_user_from_jwt(token, app, source, request)

        method_args = {
            "jwt": token,
        }
        if source:
            method_args["source"] = source
        if provider:
            method_args["provider"] = provider
        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "jwt",
                PLAN_CONTEXT_METHOD_ARGS: method_args,
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)

    def post_init_client_credentials_generated(self, request: HttpRequest):
        # Authorize user access
        app = Application.objects.filter(provider=self.provider).first()
        if not app or not app.provider:
            raise TokenError("invalid_grant")
        with audit_ignore():
            self.user, _ = User.objects.update_or_create(
                # trim username to ensure the entire username is max 150 chars
                # (22 chars being the length of the "template")
                username=f"ak-{self.provider.name[: USERNAME_MAX_LENGTH - 22]}-client_credentials",
                defaults={
                    "last_login": timezone.now(),
                    "name": f"Autogenerated user from application {app.name} (client credentials)",
                    "path": f"{USER_PATH_SYSTEM_PREFIX}/apps/{app.slug}",
                    "type": UserTypes.SERVICE_ACCOUNT,
                },
            )
            self.user.attributes[USER_ATTRIBUTE_GENERATED] = True
            self.user.save()
        self.check_policy_access(app, request)

        Event.new(
            action=EventAction.LOGIN,
            **{
                PLAN_CONTEXT_METHOD: "oauth_client_secret",
                PLAN_CONTEXT_APPLICATION: app,
            },
        ).from_http(request, user=self.user)
