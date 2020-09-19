"""passbook OAuth2 Authorization views"""
from dataclasses import dataclass, field
from typing import List, Optional, Set
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from structlog import get_logger

from passbook.core.models import Application
from passbook.flows.models import in_memory_stage
from passbook.flows.planner import (
    PLAN_CONTEXT_APPLICATION,
    PLAN_CONTEXT_SSO,
    FlowPlan,
    FlowPlanner,
)
from passbook.flows.stage import StageView
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.time import timedelta_from_string
from passbook.lib.utils.urls import redirect_with_qs
from passbook.lib.views import bad_request_message
from passbook.policies.mixins import PolicyAccessMixin
from passbook.providers.oauth2.constants import (
    PROMPT_CONSNET,
    PROMPT_NONE,
    SCOPE_OPENID,
)
from passbook.providers.oauth2.errors import (
    AuthorizeError,
    ClientIdError,
    OAuth2Error,
    RedirectUriError,
)
from passbook.providers.oauth2.models import (
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
    ResponseTypes,
)
from passbook.providers.oauth2.views.userinfo import UserInfoView
from passbook.stages.consent.models import ConsentMode, ConsentStage
from passbook.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_TEMPLATE,
    ConsentStageView,
)

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "params"
PLAN_CONTEXT_SCOPE_DESCRIPTIONS = "scope_descriptions"

ALLOWED_PROMPT_PARAMS = {PROMPT_NONE, PROMPT_CONSNET}


@dataclass
class OAuthAuthorizationParams:
    """Parameteres required to authorize an OAuth Client"""

    client_id: str
    redirect_uri: str
    response_type: str
    scope: List[str]
    state: str
    nonce: str
    prompt: Set[str]
    grant_type: str

    provider: OAuth2Provider = field(default_factory=OAuth2Provider)

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

        response_type = query_dict.get("response_type", "")
        grant_type = None
        # Determine which flow to use.
        if response_type in [ResponseTypes.CODE, ResponseTypes.CODE_ADFS]:
            grant_type = GrantTypes.AUTHORIZATION_CODE
        elif response_type in [
            ResponseTypes.ID_TOKEN,
            ResponseTypes.ID_TOKEN_TOKEN,
            ResponseTypes.CODE_TOKEN,
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
            raise AuthorizeError(
                query_dict.get("redirect_uri", ""),
                "unsupported_response_type",
                grant_type,
            )

        return OAuthAuthorizationParams(
            client_id=query_dict.get("client_id", ""),
            redirect_uri=query_dict.get("redirect_uri", ""),
            response_type=response_type,
            grant_type=grant_type,
            scope=query_dict.get("scope", "").split(),
            state=query_dict.get("state", ""),
            nonce=query_dict.get("nonce", ""),
            prompt=ALLOWED_PROMPT_PARAMS.intersection(
                set(query_dict.get("prompt", "").split())
            ),
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
        is_open_id = SCOPE_OPENID in self.scope

        # Redirect URI validation.
        if is_open_id and not self.redirect_uri:
            LOGGER.warning("Missing redirect uri.")
            raise RedirectUriError()
        if self.redirect_uri not in self.provider.redirect_uris.split():
            LOGGER.warning(
                "Invalid redirect uri",
                redirect_uri=self.redirect_uri,
                excepted=self.provider.redirect_uris.split(),
            )
            raise RedirectUriError()

        if not is_open_id and (
            self.grant_type == GrantTypes.HYBRID
            or self.response_type
            in [ResponseTypes.ID_TOKEN, ResponseTypes.ID_TOKEN_TOKEN]
        ):
            LOGGER.warning("Missing 'openid' scope.")
            raise AuthorizeError(self.redirect_uri, "invalid_scope", self.grant_type)

        # Nonce parameter validation.
        if is_open_id and self.grant_type == GrantTypes.IMPLICIT and not self.nonce:
            raise AuthorizeError(self.redirect_uri, "invalid_request", self.grant_type)

        # Response type parameter validation.
        if is_open_id:
            actual_response_type = self.provider.response_type
            if "#" in self.provider.response_type:
                hash_index = actual_response_type.index("#")
                actual_response_type = actual_response_type[:hash_index]
            if self.response_type != actual_response_type:
                raise AuthorizeError(
                    self.redirect_uri, "invalid_request", self.grant_type
                )

        # PKCE validation of the transformation method.
        if self.code_challenge:
            if not (self.code_challenge_method in ["plain", "S256"]):
                raise AuthorizeError(
                    self.redirect_uri, "invalid_request", self.grant_type
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
                )
            return redirect(self.create_response_uri())
        except (ClientIdError, RedirectUriError) as error:
            self.executor.stage_invalid()
            # pylint: disable=no-member
            return bad_request_message(request, error.description, title=error.error)
        except AuthorizeError as error:
            self.executor.stage_invalid()
            uri = error.create_uri(self.params.redirect_uri, self.params.state)
            return redirect(uri)

    def create_response_uri(self) -> str:
        """Create a final Response URI the user is redirected to."""
        uri = urlsplit(self.params.redirect_uri)
        query_params = parse_qs(uri.query)
        query_fragment = {}

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
            elif self.params.grant_type in [GrantTypes.IMPLICIT, GrantTypes.HYBRID]:
                token = self.provider.create_refresh_token(
                    user=self.request.user, scope=self.params.scope,
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
                        user=self.request.user, request=self.request,
                    )
                    id_token.nonce = self.params.nonce

                    # Include at_hash when access_token is being returned.
                    if "access_token" in query_fragment:
                        id_token.at_hash = token.at_hash

                    # Check if response_type must include id_token in the response.
                    if self.params.response_type in [
                        ResponseTypes.ID_TOKEN,
                        ResponseTypes.ID_TOKEN_TOKEN,
                        ResponseTypes.CODE_ID_TOKEN,
                        ResponseTypes.CODE_ID_TOKEN_TOKEN,
                    ]:
                        query_fragment["id_token"] = self.provider.encode(
                            id_token.to_dict()
                        )
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

        except OAuth2Error as error:
            LOGGER.exception("Error when trying to create response uri", error=error)
            raise AuthorizeError(
                self.params.redirect_uri, "server_error", self.params.grant_type
            )

        uri = uri._replace(
            query=urlencode(query_params, doseq=True),
            fragment=uri.fragment + urlencode(query_fragment, doseq=True),
        )

        return urlunsplit(uri)


class AuthorizationFlowInitView(PolicyAccessMixin, View):
    """OAuth2 Flow initializer, checks access to application and starts flow"""

    # pylint: disable=unused-argument
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Check access to application, start FlowPLanner, return to flow executor shell"""
        client_id = request.GET.get("client_id")
        # TODO: This whole block should be moved to a base class
        provider = get_object_or_404(OAuth2Provider, client_id=client_id)
        try:
            application = self.provider_to_application(provider)
        except Application.DoesNotExist:
            return self.handle_no_permission_authenticated()
        # Check if user is unauthenticated, so we pass the application
        # for the identification stage
        if not request.user.is_authenticated:
            return self.handle_no_permission(application)
        # Check permissions
        result = self.user_has_access(application)
        if not result.passing:
            return self.handle_no_permission_authenticated(result)
        # TODO: End block
        # Extract params so we can save them in the plan context
        try:
            params = OAuthAuthorizationParams.from_request(request)
        except (ClientIdError, RedirectUriError) as error:
            # pylint: disable=no-member
            return bad_request_message(request, error.description, title=error.error)
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(provider.authorization_flow)
        # planner.use_cache = False
        planner.allow_empty_flows = True
        plan: FlowPlan = planner.plan(
            self.request,
            {
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_APPLICATION: application,
                # OAuth2 related params
                PLAN_CONTEXT_PARAMS: params,
                PLAN_CONTEXT_SCOPE_DESCRIPTIONS: UserInfoView().get_scope_descriptions(
                    params.scope
                ),
                # Consent related params
                PLAN_CONTEXT_CONSENT_TEMPLATE: "providers/oauth2/consent.html",
            },
        )
        # OpenID clients can specify a `prompt` parameter, and if its set to consent we
        # need to inject a consent stage
        if PROMPT_CONSNET in params.prompt:
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
            "passbook_flows:flow-executor-shell",
            self.request.GET,
            flow_slug=provider.authorization_flow.slug,
        )
