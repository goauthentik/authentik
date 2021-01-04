"""authentik OAuth2 Authorization views"""
from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional, Set
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.events.utils import get_user
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlan,
    FlowPlanner,
)
from authentik.flows.stage import StageView
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.lib.utils.time import timedelta_from_string
from authentik.lib.utils.urls import redirect_with_qs
from authentik.lib.views import bad_request_message
from authentik.policies.views import PolicyAccessView, RequestValidationError
from authentik.providers.oauth2.constants import (
    PROMPT_CONSNET,
    PROMPT_LOGIN,
    PROMPT_NONE,
    SCOPE_OPENID,
)
from authentik.providers.oauth2.errors import (
    AuthorizeError,
    ClientIdError,
    OAuth2Error,
    RedirectUriError,
)
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
    ResponseTypes,
)
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.models import ConsentMode, ConsentStage
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_TEMPLATE,
    ConsentStageView,
)

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPE_DESCRIPTIONS = "scope_descriptions"
SESSION_NEEDS_LOGIN = "authentik_oauth2_needs_login"

ALLOWED_PROMPT_PARAMS = {PROMPT_NONE, PROMPT_CONSNET, PROMPT_LOGIN}


@dataclass
# pylint: disable=too-many-instance-attributes
class OAuthAuthorizationParams:
    """Parameteres required to authorize an OAuth Client"""

    client_id: str
    redirect_uri: str
    response_type: str
    scope: List[str]
    state: str
    nonce: Optional[str]
    prompt: Set[str]
    grant_type: str

    provider: OAuth2Provider = field(default_factory=OAuth2Provider)

    request: Optional[str] = None

    max_age: Optional[int] = None

    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None

    @staticmethod
    def from_request(request: HttpRequest) -> "OAuthAuthorizationParams":
        """
        Get all the params used by the Authorization Code Flow
        (and also for the Implicit and Hybrid).

        See: http://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
        """
        # Because in this endpoint we handle both GET
        # and POST request.
        query_dict = request.POST if request.method == "POST" else request.GET
        state = query_dict.get("state")
        redirect_uri = query_dict.get("redirect_uri", "")

        response_type = query_dict.get("response_type", "")
        grant_type = None
        # Determine which flow to use.
        if response_type in [ResponseTypes.CODE]:
            grant_type = GrantTypes.AUTHORIZATION_CODE
        elif response_type in [
            ResponseTypes.ID_TOKEN,
            ResponseTypes.ID_TOKEN_TOKEN,
        ]:
            grant_type = GrantTypes.IMPLICIT
        elif response_type in [
            ResponseTypes.CODE_TOKEN,
            ResponseTypes.CODE_ID_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
        ]:
            grant_type = GrantTypes.HYBRID

        # Grant type validation.
        if not grant_type:
            LOGGER.warning("Invalid response type", type=response_type)
            raise AuthorizeError(redirect_uri, "unsupported_response_type", "", state)

        max_age = query_dict.get("max_age")
        return OAuthAuthorizationParams(
            client_id=query_dict.get("client_id", ""),
            redirect_uri=redirect_uri,
            response_type=response_type,
            grant_type=grant_type,
            scope=query_dict.get("scope", "").split(),
            state=state,
            nonce=query_dict.get("nonce"),
            prompt=ALLOWED_PROMPT_PARAMS.intersection(
                set(query_dict.get("prompt", "").split())
            ),
            request=query_dict.get("request", None),
            max_age=int(max_age) if max_age else None,
            code_challenge=query_dict.get("code_challenge"),
            code_challenge_method=query_dict.get("code_challenge_method"),
        )

    def __post_init__(self):
        try:
            self.provider: OAuth2Provider = OAuth2Provider.objects.get(
                client_id=self.client_id
            )
        except OAuth2Provider.DoesNotExist:
            LOGGER.warning("Invalid client identifier", client_id=self.client_id)
            raise ClientIdError()
        self.check_redirect_uri()
        self.check_scope()
        self.check_nonce()
        self.check_code_challenge()

    def check_redirect_uri(self):
        """Redirect URI validation."""
        if not self.redirect_uri:
            LOGGER.warning("Missing redirect uri.")
            raise RedirectUriError()
        if self.redirect_uri.lower() not in [
            x.lower() for x in self.provider.redirect_uris.split()
        ]:
            Event.new(
                EventAction.CONFIGURATION_ERROR,
                provider=self.provider,
                message="Invalid redirect URI was used.",
                client_used=self.redirect_uri,
                configured=self.provider.redirect_uris.split(),
            ).save()
            LOGGER.warning(
                "Invalid redirect uri",
                redirect_uri=self.redirect_uri,
                excepted=self.provider.redirect_uris.split(),
            )
            raise RedirectUriError()

        if self.request:
            raise AuthorizeError(
                self.redirect_uri, "request_not_supported", self.grant_type, self.state
            )

    def check_scope(self):
        """Ensure openid scope is set in Hybrid flows, or when requesting an id_token"""
        if SCOPE_OPENID not in self.scope and (
            self.grant_type == GrantTypes.HYBRID
            or self.response_type
            in [ResponseTypes.ID_TOKEN, ResponseTypes.ID_TOKEN_TOKEN]
        ):
            LOGGER.warning("Missing 'openid' scope.")
            raise AuthorizeError(
                self.redirect_uri, "invalid_scope", self.grant_type, self.state
            )

    def check_nonce(self):
        """Nonce parameter validation."""
        if not self.nonce:
            self.nonce = self.state
            LOGGER.warning("Using state as nonce for OpenID Request")
        if not self.nonce:
            if SCOPE_OPENID in self.scope:
                LOGGER.warning("Missing nonce for OpenID Request")
                raise AuthorizeError(
                    self.redirect_uri, "invalid_request", self.grant_type, self.state
                )

    def check_code_challenge(self):
        """PKCE validation of the transformation method."""
        if self.code_challenge:
            if not (self.code_challenge_method in ["plain", "S256"]):
                raise AuthorizeError(
                    self.redirect_uri, "invalid_request", self.grant_type, self.state
                )

    def create_code(self, request: HttpRequest) -> AuthorizationCode:
        """Create an AuthorizationCode object for the request"""
        code = AuthorizationCode()
        code.user = request.user
        code.provider = self.provider

        code.code = uuid4().hex

        if self.code_challenge and self.code_challenge_method:
            code.code_challenge = self.code_challenge
            code.code_challenge_method = self.code_challenge_method

        code.expires_at = timezone.now() + timedelta_from_string(
            self.provider.token_validity
        )
        code.scope = self.scope
        code.nonce = self.nonce
        code.is_open_id = SCOPE_OPENID in self.scope

        return code


class OAuthFulfillmentStage(StageView):
    """Final stage, restores params from Flow."""

    params: OAuthAuthorizationParams
    provider: OAuth2Provider

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.params: OAuthAuthorizationParams = self.executor.plan.context.pop(
            PLAN_CONTEXT_PARAMS
        )
        application: Application = self.executor.plan.context.pop(
            PLAN_CONTEXT_APPLICATION
        )
        self.provider = get_object_or_404(OAuth2Provider, pk=application.provider_id)
        try:
            # At this point we don't need to check permissions anymore
            if {PROMPT_NONE, PROMPT_CONSNET}.issubset(self.params.prompt):
                raise AuthorizeError(
                    self.params.redirect_uri,
                    "consent_required",
                    self.params.grant_type,
                    self.params.state,
                )
            Event.new(
                EventAction.AUTHORIZE_APPLICATION,
                authorized_application=application,
                flow=self.executor.plan.flow_pk,
            ).from_http(self.request)
            return redirect(self.create_response_uri())
        except (ClientIdError, RedirectUriError) as error:
            self.executor.stage_invalid()
            # pylint: disable=no-member
            return bad_request_message(request, error.description, title=error.error)
        except AuthorizeError as error:
            self.executor.stage_invalid()
            return redirect(error.create_uri())

    def create_response_uri(self) -> str:
        """Create a final Response URI the user is redirected to."""
        uri = urlsplit(self.params.redirect_uri)
        query_params = parse_qs(uri.query)

        try:
            code = None

            if self.params.grant_type in [
                GrantTypes.AUTHORIZATION_CODE,
                GrantTypes.HYBRID,
            ]:
                code = self.params.create_code(self.request)
                code.save()

            if self.params.grant_type == GrantTypes.AUTHORIZATION_CODE:
                query_params["code"] = code.code
                query_params["state"] = [
                    str(self.params.state) if self.params.state else ""
                ]

                uri = uri._replace(query=urlencode(query_params, doseq=True))
                return urlunsplit(uri)
            if self.params.grant_type in [GrantTypes.IMPLICIT, GrantTypes.HYBRID]:
                query_fragment = self.create_implicit_response(code)

                uri = uri._replace(
                    fragment=uri.fragment + urlencode(query_fragment, doseq=True),
                )
                return urlunsplit(uri)
            raise OAuth2Error()
        except OAuth2Error as error:
            LOGGER.exception("Error when trying to create response uri", error=error)
            raise AuthorizeError(
                self.params.redirect_uri,
                "server_error",
                self.params.grant_type,
                self.params.state,
            )

    def create_implicit_response(self, code: Optional[AuthorizationCode]) -> dict:
        """Create implicit response's URL Fragment dictionary"""
        query_fragment = {}

        token = self.provider.create_refresh_token(
            user=self.request.user,
            scope=self.params.scope,
            request=self.request,
        )

        # Check if response_type must include access_token in the response.
        if self.params.response_type in [
            ResponseTypes.ID_TOKEN_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
            ResponseTypes.ID_TOKEN,
            ResponseTypes.CODE_TOKEN,
        ]:
            query_fragment["access_token"] = token.access_token

        # We don't need id_token if it's an OAuth2 request.
        if SCOPE_OPENID in self.params.scope:
            id_token = token.create_id_token(
                user=self.request.user,
                request=self.request,
            )
            id_token.nonce = self.params.nonce

            # Include at_hash when access_token is being returned.
            if "access_token" in query_fragment:
                id_token.at_hash = token.at_hash

            if self.params.response_type in [
                ResponseTypes.CODE_ID_TOKEN,
                ResponseTypes.CODE_ID_TOKEN_TOKEN,
            ]:
                id_token.c_hash = code.c_hash

            # Check if response_type must include id_token in the response.
            if self.params.response_type in [
                ResponseTypes.ID_TOKEN,
                ResponseTypes.ID_TOKEN_TOKEN,
                ResponseTypes.CODE_ID_TOKEN,
                ResponseTypes.CODE_ID_TOKEN_TOKEN,
            ]:
                query_fragment["id_token"] = self.provider.encode(id_token.to_dict())
            token.id_token = id_token

        # Store the token.
        token.save()

        # Code parameter must be present if it's Hybrid Flow.
        if self.params.grant_type == GrantTypes.HYBRID:
            query_fragment["code"] = code.code

        query_fragment["token_type"] = "bearer"
        query_fragment["expires_in"] = timedelta_from_string(
            self.provider.token_validity
        ).seconds
        query_fragment["state"] = self.params.state if self.params.state else ""

        return query_fragment


class AuthorizationFlowInitView(PolicyAccessView):
    """OAuth2 Flow initializer, checks access to application and starts flow"""

    params: OAuthAuthorizationParams

    def pre_permission_check(self):
        """Check prompt parameter before checking permission/authentication,
        see https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.3.1.2.6"""
        try:
            self.params = OAuthAuthorizationParams.from_request(self.request)
        except AuthorizeError as error:
            raise RequestValidationError(redirect(error.create_uri()))
        except OAuth2Error as error:
            raise RequestValidationError(
                bad_request_message(self.request, error.description, title=error.error)
            )
        except OAuth2Provider.DoesNotExist:
            raise Http404
        if PROMPT_NONE in self.params.prompt and not self.request.user.is_authenticated:
            # When "prompt" is set to "none" but the user is not logged in, show an error message
            error = AuthorizeError(
                self.params.redirect_uri,
                "login_required",
                self.params.grant_type,
                self.params.state,
            )
            raise RequestValidationError(redirect(error.create_uri()))

    def resolve_provider_application(self):
        client_id = self.request.GET.get("client_id")
        self.provider = get_object_or_404(OAuth2Provider, client_id=client_id)
        self.application = self.provider.application

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Start FlowPLanner, return to flow executor shell"""
        # After we've checked permissions, and the user has access, check if we need
        # to re-authenticate the user
        if self.params.max_age:
            current_age: timedelta = (
                timezone.now()
                - Event.objects.filter(
                    action=EventAction.LOGIN, user=get_user(self.request.user)
                )
                .latest("created")
                .created
            )
            if current_age.total_seconds() > self.params.max_age:
                return self.handle_no_permission()
        # If prompt=login, we need to re-authenticate the user regardless
        if (
            PROMPT_LOGIN in self.params.prompt
            and SESSION_NEEDS_LOGIN not in self.request.session
        ):
            self.request.session[SESSION_NEEDS_LOGIN] = True
            return self.handle_no_permission()
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        # planner.use_cache = False
        planner.allow_empty_flows = True
        plan: FlowPlan = planner.plan(
            self.request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: self.application,
                # OAuth2 related params
                PLAN_CONTEXT_PARAMS: self.params,
                PLAN_CONTEXT_SCOPE_DESCRIPTIONS: UserInfoView().get_scope_descriptions(
                    self.params.scope
                ),
                # Consent related params
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/oauth2/consent.html",
            },
        )
        # OpenID clients can specify a `prompt` parameter, and if its set to consent we
        # need to inject a consent stage
        if PROMPT_CONSNET in self.params.prompt:
            if not any([isinstance(x, ConsentStageView) for x in plan.stages]):
                # Plan does not have any consent stage, so we add an in-memory one
                stage = ConsentStage(
                    name="OAuth2 Provider In-memory consent stage",
                    mode=ConsentMode.ALWAYS_REQUIRE,
                )
                plan.append(stage)
        plan.append(in_memory_stage(OAuthFulfillmentStage))
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=self.provider.authorization_flow.slug,
        )
