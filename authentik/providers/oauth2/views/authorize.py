"""authentik OAuth2 Authorization views"""
from dataclasses import dataclass, field
from datetime import timedelta
from json import dumps
from re import error as RegexError
from re import fullmatch
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlsplit, urlunsplit
from uuid import uuid4

from django.http import HttpRequest, HttpResponse
from django.http.response import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import Application
from authentik.events.models import Event, EventAction
from authentik.events.signals import get_login_event
from authentik.flows.challenge import (
    PLAN_CONTEXT_TITLE,
    AutosubmitChallenge,
    ChallengeTypes,
    HttpChallengeResponse,
)
from authentik.flows.exceptions import FlowNonApplicableException
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, PLAN_CONTEXT_SSO, FlowPlanner
from authentik.flows.stage import StageView
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.utils.time import timedelta_from_string
from authentik.lib.utils.urls import redirect_with_qs
from authentik.lib.views import bad_request_message
from authentik.policies.types import PolicyRequest
from authentik.policies.views import PolicyAccessView, RequestValidationError
from authentik.providers.oauth2.constants import (
    PKCE_METHOD_PLAIN,
    PKCE_METHOD_S256,
    PROMPT_CONSENT,
    PROMPT_LOGIN,
    PROMPT_NONE,
    SCOPE_OPENID,
    TOKEN_TYPE,
)
from authentik.providers.oauth2.errors import (
    AuthorizeError,
    ClientIdError,
    OAuth2Error,
    RedirectUriError,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
    ResponseMode,
    ResponseTypes,
    ScopeMapping,
)
from authentik.providers.oauth2.utils import HttpResponseRedirectScheme
from authentik.providers.oauth2.views.userinfo import UserInfoView
from authentik.stages.consent.models import ConsentMode, ConsentStage
from authentik.stages.consent.stage import (
    PLAN_CONTEXT_CONSENT_HEADER,
    PLAN_CONTEXT_CONSENT_PERMISSIONS,
    ConsentStageView,
)

LOGGER = get_logger()

PLAN_CONTEXT_PARAMS = "goauthentik.io/providers/oauth2/params"
SESSION_KEY_LAST_LOGIN_UID = "authentik/providers/oauth2/last_login_uid"

ALLOWED_PROMPT_PARAMS = {PROMPT_NONE, PROMPT_CONSENT, PROMPT_LOGIN}


@dataclass(slots=True)
# pylint: disable=too-many-instance-attributes
class OAuthAuthorizationParams:
    """Parameters required to authorize an OAuth Client"""

    client_id: str
    redirect_uri: str
    response_type: str
    response_mode: Optional[str]
    scope: list[str]
    state: str
    nonce: Optional[str]
    prompt: set[str]
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

        # Validate and check the response_mode against the predefined dict
        # Set to Query or Fragment if not defined in request
        response_mode = query_dict.get("response_mode", False)

        if response_mode not in ResponseMode.values:
            response_mode = ResponseMode.QUERY

            if grant_type in [GrantTypes.IMPLICIT, GrantTypes.HYBRID]:
                response_mode = ResponseMode.FRAGMENT

        max_age = query_dict.get("max_age")
        return OAuthAuthorizationParams(
            client_id=query_dict.get("client_id", ""),
            redirect_uri=redirect_uri,
            response_type=response_type,
            response_mode=response_mode,
            grant_type=grant_type,
            scope=query_dict.get("scope", "").split(),
            state=state,
            nonce=query_dict.get("nonce"),
            prompt=ALLOWED_PROMPT_PARAMS.intersection(set(query_dict.get("prompt", "").split())),
            request=query_dict.get("request", None),
            max_age=int(max_age) if max_age else None,
            code_challenge=query_dict.get("code_challenge"),
            code_challenge_method=query_dict.get("code_challenge_method", "plain"),
        )

    def __post_init__(self):
        self.provider: OAuth2Provider = OAuth2Provider.objects.filter(
            client_id=self.client_id
        ).first()
        if not self.provider:
            LOGGER.warning("Invalid client identifier", client_id=self.client_id)
            raise ClientIdError(client_id=self.client_id)
        self.check_redirect_uri()
        self.check_scope()
        self.check_nonce()
        self.check_code_challenge()

    def check_redirect_uri(self):
        """Redirect URI validation."""
        allowed_redirect_urls = self.provider.redirect_uris.split()
        if not self.redirect_uri:
            LOGGER.warning("Missing redirect uri.")
            raise RedirectUriError("", allowed_redirect_urls)

        if self.provider.redirect_uris == "":
            LOGGER.info("Setting redirect for blank redirect_uris", redirect=self.redirect_uri)
            self.provider.redirect_uris = self.redirect_uri
            self.provider.save()
            allowed_redirect_urls = self.provider.redirect_uris.split()

        if self.provider.redirect_uris == "*":
            LOGGER.info("Converting redirect_uris to regex", redirect=self.redirect_uri)
            self.provider.redirect_uris = ".*"
            self.provider.save()
            allowed_redirect_urls = self.provider.redirect_uris.split()

        try:
            if not any(fullmatch(x, self.redirect_uri) for x in allowed_redirect_urls):
                LOGGER.warning(
                    "Invalid redirect uri (regex comparison)",
                    redirect_uri=self.redirect_uri,
                    expected=allowed_redirect_urls,
                )
                raise RedirectUriError(self.redirect_uri, allowed_redirect_urls)
        except RegexError as exc:
            LOGGER.info("Failed to parse regular expression, checking directly", exc=exc)
            if not any(x == self.redirect_uri for x in allowed_redirect_urls):
                LOGGER.warning(
                    "Invalid redirect uri (strict comparison)",
                    redirect_uri=self.redirect_uri,
                    expected=allowed_redirect_urls,
                )
                raise RedirectUriError(self.redirect_uri, allowed_redirect_urls)
        if self.request:
            raise AuthorizeError(
                self.redirect_uri, "request_not_supported", self.grant_type, self.state
            )

    def check_scope(self):
        """Ensure openid scope is set in Hybrid flows, or when requesting an id_token"""
        if len(self.scope) == 0:
            default_scope_names = set(
                ScopeMapping.objects.filter(provider__in=[self.provider]).values_list(
                    "scope_name", flat=True
                )
            )
            self.scope = default_scope_names
            LOGGER.info(
                "No scopes requested, defaulting to all configured scopes", scopes=self.scope
            )
        if SCOPE_OPENID not in self.scope and (
            self.grant_type == GrantTypes.HYBRID
            or self.response_type in [ResponseTypes.ID_TOKEN, ResponseTypes.ID_TOKEN_TOKEN]
        ):
            LOGGER.warning("Missing 'openid' scope.")
            raise AuthorizeError(self.redirect_uri, "invalid_scope", self.grant_type, self.state)

    def check_nonce(self):
        """Nonce parameter validation."""
        # nonce is required for all flows that return an id_token from the authorization endpoint,
        # see https://openid.net/specs/openid-connect-core-1_0.html#ImplicitAuthRequest or
        # https://openid.net/specs/openid-connect-core-1_0.html#HybridIDToken and
        # https://bitbucket.org/openid/connect/issues/972/nonce-requirement-in-hybrid-auth-request
        if self.response_type not in [
            ResponseTypes.ID_TOKEN,
            ResponseTypes.ID_TOKEN_TOKEN,
            ResponseTypes.CODE_ID_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
        ]:
            return
        if SCOPE_OPENID not in self.scope:
            return
        if not self.nonce:
            LOGGER.warning("Missing nonce for OpenID Request")
            raise AuthorizeError(self.redirect_uri, "invalid_request", self.grant_type, self.state)

    def check_code_challenge(self):
        """PKCE validation of the transformation method."""
        if self.code_challenge and self.code_challenge_method not in [
            PKCE_METHOD_PLAIN,
            PKCE_METHOD_S256,
        ]:
            raise AuthorizeError(
                self.redirect_uri,
                "invalid_request",
                self.grant_type,
                self.state,
                f"Unsupported challenge method {self.code_challenge_method}",
            )

    def create_code(self, request: HttpRequest) -> AuthorizationCode:
        """Create an AuthorizationCode object for the request"""
        auth_event = get_login_event(request)

        now = timezone.now()

        code = AuthorizationCode(
            user=request.user,
            provider=self.provider,
            auth_time=auth_event.created if auth_event else now,
            code=uuid4().hex,
            expires=now + timedelta_from_string(self.provider.access_code_validity),
            scope=self.scope,
            nonce=self.nonce,
        )

        if self.code_challenge and self.code_challenge_method:
            code.code_challenge = self.code_challenge
            code.code_challenge_method = self.code_challenge_method

        return code


class AuthorizationFlowInitView(PolicyAccessView):
    """OAuth2 Flow initializer, checks access to application and starts flow"""

    params: OAuthAuthorizationParams

    def pre_permission_check(self):
        """Check prompt parameter before checking permission/authentication,
        see https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.3.1.2.6"""
        # Quick sanity check at the beginning to prevent event spamming
        if len(self.request.GET) < 1:
            raise Http404
        try:
            self.params = OAuthAuthorizationParams.from_request(self.request)
        except AuthorizeError as error:
            LOGGER.warning(error.description, redirect_uri=error.redirect_uri)
            raise RequestValidationError(error.get_response(self.request))
        except OAuth2Error as error:
            LOGGER.warning(error.description)
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
            raise RequestValidationError(error.get_response(self.request))

    def resolve_provider_application(self):
        client_id = self.request.GET.get("client_id")
        self.provider = get_object_or_404(OAuth2Provider, client_id=client_id)
        self.application = self.provider.application

    def modify_policy_request(self, request: PolicyRequest) -> PolicyRequest:
        request.context["oauth_scopes"] = self.params.scope
        request.context["oauth_grant_type"] = self.params.grant_type
        request.context["oauth_code_challenge"] = self.params.code_challenge
        request.context["oauth_code_challenge_method"] = self.params.code_challenge_method
        request.context["oauth_max_age"] = self.params.max_age
        request.context["oauth_redirect_uri"] = self.params.redirect_uri
        request.context["oauth_response_type"] = self.params.response_type
        return request

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Start FlowPLanner, return to flow executor shell"""
        # Require a login event to be set, otherwise make the user re-login
        login_event = get_login_event(request)
        if not login_event:
            LOGGER.warning("request with no login event")
            return self.handle_no_permission()
        login_uid = str(login_event.pk)
        # After we've checked permissions, and the user has access, check if we need
        # to re-authenticate the user
        if self.params.max_age:
            # Attempt to check via the session's login event if set, otherwise we can't
            # check
            login_time = login_event.created
            current_age: timedelta = timezone.now() - login_time
            if current_age.total_seconds() > self.params.max_age:
                LOGGER.debug(
                    "Triggering authentication as max_age requirement",
                    max_age=self.params.max_age,
                    ago=int(current_age.total_seconds()),
                )
                # Since we already need to re-authenticate the user, set the old login UID
                # in case this request has both max_age and prompt=login
                self.request.session[SESSION_KEY_LAST_LOGIN_UID] = login_uid
                return self.handle_no_permission()
        # If prompt=login, we need to re-authenticate the user regardless
        # Check if we're not already doing the re-authentication
        if PROMPT_LOGIN in self.params.prompt:
            # No previous login UID saved, so save the current uid and trigger
            # re-login, or previous login UID matches current one, so no re-login happened yet
            if (
                SESSION_KEY_LAST_LOGIN_UID not in self.request.session
                or login_uid == self.request.session[SESSION_KEY_LAST_LOGIN_UID]
            ):
                self.request.session[SESSION_KEY_LAST_LOGIN_UID] = login_uid
                return self.handle_no_permission()
        scope_descriptions = UserInfoView().get_scope_descriptions(self.params.scope)
        # Regardless, we start the planner and return to it
        planner = FlowPlanner(self.provider.authorization_flow)
        planner.allow_empty_flows = True
        try:
            plan = planner.plan(
                self.request,
                {
                    PLAN_CONTEXT_SSO: True,
                    PLAN_CONTEXT_APPLICATION: self.application,
                    # OAuth2 related params
                    PLAN_CONTEXT_PARAMS: self.params,
                    # Consent related params
                    PLAN_CONTEXT_CONSENT_HEADER: _("You're about to sign into %(application)s.")
                    % {"application": self.application.name},
                    PLAN_CONTEXT_CONSENT_PERMISSIONS: scope_descriptions,
                },
            )
        except FlowNonApplicableException:
            return self.handle_no_permission_authenticated()
        # OpenID clients can specify a `prompt` parameter, and if its set to consent we
        # need to inject a consent stage
        if PROMPT_CONSENT in self.params.prompt:
            if not any(isinstance(x.stage, ConsentStageView) for x in plan.bindings):
                # Plan does not have any consent stage, so we add an in-memory one
                stage = ConsentStage(
                    name="OAuth2 Provider In-memory consent stage",
                    mode=ConsentMode.ALWAYS_REQUIRE,
                )
                plan.append_stage(stage)

        plan.append_stage(in_memory_stage(OAuthFulfillmentStage))

        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=self.provider.authorization_flow.slug,
        )


class OAuthFulfillmentStage(StageView):
    """Final stage, restores params from Flow."""

    params: OAuthAuthorizationParams
    provider: OAuth2Provider
    application: Application

    def redirect(self, uri: str) -> HttpResponse:
        """Redirect using HttpResponseRedirectScheme, compatible with non-http schemes"""
        parsed = urlparse(uri)

        if self.params.response_mode == ResponseMode.FORM_POST:
            # parse_qs returns a dictionary with values wrapped in lists, however
            # we need a flat dictionary for the autosubmit challenge

            # this picks the first item in the list if the value is a list,
            # otherwise just the value as-is
            query_params = dict(
                (k, v[0] if isinstance(v, list) else v) for k, v in parse_qs(parsed.query).items()
            )

            challenge = AutosubmitChallenge(
                data={
                    "type": ChallengeTypes.NATIVE.value,
                    "component": "ak-stage-autosubmit",
                    "title": self.executor.plan.context.get(
                        PLAN_CONTEXT_TITLE,
                        _("Redirecting to %(app)s..." % {"app": self.application.name}),
                    ),
                    "url": self.params.redirect_uri,
                    "attrs": query_params,
                }
            )

            challenge.is_valid()

            return HttpChallengeResponse(
                challenge=challenge,
            )

        return HttpResponseRedirectScheme(uri, allowed_schemes=[parsed.scheme])

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Wrapper when this stage gets hit with a post request"""
        return self.get(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """final Stage of an OAuth2 Flow"""
        if PLAN_CONTEXT_PARAMS not in self.executor.plan.context:
            LOGGER.warning("Got to fulfillment stage with no pending context")
            return HttpResponseBadRequest()
        self.params: OAuthAuthorizationParams = self.executor.plan.context.pop(PLAN_CONTEXT_PARAMS)
        self.application: Application = self.executor.plan.context.pop(PLAN_CONTEXT_APPLICATION)
        self.provider = get_object_or_404(OAuth2Provider, pk=self.application.provider_id)
        try:
            # At this point we don't need to check permissions anymore
            if {PROMPT_NONE, PROMPT_CONSENT}.issubset(self.params.prompt):
                raise AuthorizeError(
                    self.params.redirect_uri,
                    "consent_required",
                    self.params.grant_type,
                    self.params.state,
                )
            Event.new(
                EventAction.AUTHORIZE_APPLICATION,
                authorized_application=self.application,
                flow=self.executor.plan.flow_pk,
                scopes=" ".join(self.params.scope),
            ).from_http(self.request)
            return self.redirect(self.create_response_uri())
        except (ClientIdError, RedirectUriError) as error:
            error.to_event(application=self.application).from_http(request)
            self.executor.stage_invalid()
            # pylint: disable=no-member
            return bad_request_message(request, error.description, title=error.error)
        except AuthorizeError as error:
            error.to_event(application=self.application).from_http(request)
            self.executor.stage_invalid()
            return error.get_response(self.request)

    def create_response_uri(self) -> str:
        """Create a final Response URI the user is redirected to."""
        uri = urlsplit(self.params.redirect_uri)

        try:
            code = None

            if self.params.grant_type in [
                GrantTypes.AUTHORIZATION_CODE,
                GrantTypes.HYBRID,
            ]:
                code = self.params.create_code(self.request)
                code.save()

            if self.params.response_mode == ResponseMode.QUERY:
                query_params = parse_qs(uri.query)
                query_params["code"] = code.code
                query_params["state"] = [str(self.params.state) if self.params.state else ""]

                uri = uri._replace(query=urlencode(query_params, doseq=True))
                return urlunsplit(uri)

            if self.params.response_mode == ResponseMode.FRAGMENT:
                query_fragment = {}
                if self.params.grant_type in [GrantTypes.AUTHORIZATION_CODE]:
                    query_fragment["code"] = code.code
                    query_fragment["state"] = [str(self.params.state) if self.params.state else ""]
                else:
                    query_fragment = self.create_implicit_response(code)

                uri = uri._replace(
                    fragment=uri.fragment + urlencode(query_fragment, doseq=True),
                )

                return urlunsplit(uri)

            if self.params.response_mode == ResponseMode.FORM_POST:
                post_params = {}
                if self.params.grant_type in [GrantTypes.AUTHORIZATION_CODE]:
                    post_params["code"] = code.code
                    post_params["state"] = [str(self.params.state) if self.params.state else ""]
                else:
                    post_params = self.create_implicit_response(code)

                uri = uri._replace(query=urlencode(post_params, doseq=True))

                return urlunsplit(uri)

            raise OAuth2Error()
        except OAuth2Error as error:
            LOGGER.warning("Error when trying to create response uri", error=error)
            raise AuthorizeError(
                self.params.redirect_uri,
                "server_error",
                self.params.grant_type,
                self.params.state,
            )

    def create_implicit_response(self, code: Optional[AuthorizationCode]) -> dict:
        """Create implicit response's URL Fragment dictionary"""
        query_fragment = {}
        auth_event = get_login_event(self.request)

        now = timezone.now()
        access_token_expiry = now + timedelta_from_string(self.provider.access_token_validity)
        token = AccessToken(
            user=self.request.user,
            scope=self.params.scope,
            expires=access_token_expiry,
            provider=self.provider,
            auth_time=auth_event.created if auth_event else now,
        )

        id_token = IDToken.new(self.provider, token, self.request)
        id_token.nonce = self.params.nonce

        if self.params.response_type in [
            ResponseTypes.CODE_ID_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
        ]:
            id_token.c_hash = code.c_hash
        token.id_token = id_token

        # Check if response_type must include access_token in the response.
        if self.params.response_type in [
            ResponseTypes.ID_TOKEN_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
            ResponseTypes.ID_TOKEN,
            ResponseTypes.CODE_TOKEN,
        ]:
            query_fragment["access_token"] = token.token
            # Get at_hash of the current token and update the id_token
            id_token.at_hash = token.at_hash

        # Check if response_type must include id_token in the response.
        if self.params.response_type in [
            ResponseTypes.ID_TOKEN,
            ResponseTypes.ID_TOKEN_TOKEN,
            ResponseTypes.CODE_ID_TOKEN,
            ResponseTypes.CODE_ID_TOKEN_TOKEN,
        ]:
            query_fragment["id_token"] = self.provider.encode(id_token.to_dict())
            token._id_token = dumps(id_token.to_dict())

        token.save()

        # Code parameter must be present if it's Hybrid Flow.
        if self.params.grant_type == GrantTypes.HYBRID:
            query_fragment["code"] = code.code

        query_fragment["token_type"] = TOKEN_TYPE
        query_fragment["expires_in"] = int(
            timedelta_from_string(self.provider.access_token_validity).total_seconds()
        )
        query_fragment["state"] = self.params.state if self.params.state else ""
        return query_fragment
