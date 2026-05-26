"""OAuth2 account selection flow stage."""

from typing import Protocol
from urllib.parse import urlencode

from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import reverse
from rest_framework.fields import BooleanField, CharField, ChoiceField
from structlog.stdlib import get_logger

from authentik.common.oauth.constants import QS_LOGIN_HINT
from authentik.core.account_selection import (
    QS_ACCOUNT_UID,
    QS_ADD_ACCOUNT,
    get_known_account_users,
)
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Application, User
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER, ChallengeStageView
from authentik.lib.avatars import get_avatar
from authentik.providers.oauth2.views.flow_context import PLAN_CONTEXT_PARAMS

LOGGER = get_logger()
COMPONENT = "ak-stage-oauth-account-selection"


class OAuthAuthorizationParamsProtocol(Protocol):
    """OAuth authorization params needed to rebuild an authorize request."""

    response_type: str
    client_id: str
    redirect_uri: str
    scope: set[str]
    state: str
    response_mode: str | None
    nonce: str | None
    prompt: set[str]
    max_age: int | None
    code_challenge: str | None
    code_challenge_method: str | None


class OAuthAccountSelectionUser(PassiveSerializer):
    """Account shown by the OAuth account selection stage."""

    uid = CharField()
    username = CharField()
    name = CharField(allow_blank=True)
    email = CharField(allow_blank=True)
    avatar = CharField()
    is_current = BooleanField()


class OAuthAccountSelectionChallenge(Challenge):
    """Challenge for selecting which account to authorize with."""

    component = CharField(default=COMPONENT)
    application_name = CharField()
    accounts = OAuthAccountSelectionUser(many=True)


class OAuthAccountSelectionChallengeResponse(ChallengeResponse):
    """OAuth account selection response."""

    component = CharField(default=COMPONENT)
    action = ChoiceField(choices=["continue", "login", "switch"])
    selected_account = CharField(required=False, allow_blank=True)


class OAuthAccountSelectionStage(ChallengeStageView):
    """OAuth account selection stage."""

    response_class = OAuthAccountSelectionChallengeResponse

    def get_account_users(self) -> list[User]:
        """Get known users for this browser session in the order they should be shown."""
        current_account = []
        if self.request.user.is_authenticated:
            current_account.append(self.request.user.uuid.hex)
        return get_known_account_users(self.request, current_account)

    def serialize_account(self, user: User) -> dict[str, object]:
        """Serialize a selectable account."""
        is_current = (
            self.request.user.is_authenticated
            and not isinstance(self.request.user, AnonymousUser)
            and user.pk == self.request.user.pk
        )
        return {
            "uid": user.uuid.hex,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "avatar": get_avatar(user, self.request),
            "is_current": is_current,
        }

    def get_challenge(self) -> OAuthAccountSelectionChallenge:
        """Show the current account and any other accounts remembered for this browser."""
        application = self.executor.plan.context.get(PLAN_CONTEXT_APPLICATION, Application())
        accounts = [self.serialize_account(user) for user in self.get_account_users()]
        return OAuthAccountSelectionChallenge(
            data={
                "component": COMPONENT,
                "application_name": application.name,
                "accounts": accounts,
            }
        )

    def is_oauth_authorization_plan(self) -> bool:
        """Check if this selector is running inside an OAuth authorization flow."""
        return PLAN_CONTEXT_PARAMS in self.executor.plan.context

    def get_authorize_query(
        self,
        login_hint: str | None = None,
        account_uid: str | None = None,
    ) -> dict[str, str]:
        """Build an authorize query from the original OAuth request."""
        params: OAuthAuthorizationParamsProtocol | None = self.executor.plan.context.get(
            PLAN_CONTEXT_PARAMS
        )
        if not params:
            query = {key: self.request.GET[key] for key in self.request.GET if key != "inspector"}
        else:
            query = {
                "response_type": params.response_type,
                "client_id": params.client_id,
                "redirect_uri": params.redirect_uri,
                "scope": " ".join(sorted(params.scope)),
            }
            optional_params = {
                "state": params.state,
                "response_mode": params.response_mode,
                "nonce": params.nonce,
                "prompt": " ".join(sorted(params.prompt)) if params.prompt else None,
                "max_age": str(params.max_age) if params.max_age else None,
                "code_challenge": params.code_challenge,
                "code_challenge_method": (
                    params.code_challenge_method if params.code_challenge else None
                ),
            }
            query.update(
                {key: value for key, value in optional_params.items() if value not in [None, ""]}
            )
        if login_hint:
            query[QS_LOGIN_HINT] = login_hint
        if account_uid:
            query[QS_ACCOUNT_UID] = account_uid
        return query

    def get_authorize_url(
        self,
        login_hint: str | None = None,
        account_uid: str | None = None,
    ) -> str:
        """Build the OAuth authorize URL from the original request."""
        query = self.get_authorize_query(login_hint, account_uid)
        url = reverse("authentik_providers_oauth2:authorize")
        if query:
            return f"{url}?{urlencode(query)}"
        return url

    def redirect_to_default_authentication(self, query: dict[str, str]) -> HttpResponse:
        """Redirect to the default authentication flow and cancel this selector."""
        self.executor.cancel()
        return HttpResponseRedirect(
            f"{reverse('authentik_flows:default-authentication')}?{urlencode(query)}"
        )

    def redirect_to_account_session(
        self,
        login_hint: str,
        account_uid: str,
    ) -> HttpResponse:
        """Switch to a live account session, then restart the OAuth request."""
        return self.redirect_to_default_authentication(
            {
                "next": self.get_authorize_url(login_hint, account_uid),
                QS_ACCOUNT_UID: account_uid,
                QS_LOGIN_HINT: login_hint,
            }
        )

    def redirect_to_add_account(self) -> HttpResponse:
        """Start OAuth authentication in a fresh session for another account."""
        return self.redirect_to_default_authentication(
            {"next": self.get_authorize_url(), QS_ADD_ACCOUNT: "true"}
        )

    def use_another_account(self) -> HttpResponse:
        """Start login for an account that is not currently remembered."""
        if self.is_oauth_authorization_plan():
            return self.redirect_to_add_account()
        return self.executor.stage_ok()

    def switch_to_account(self, selected_account: str) -> HttpResponse:
        """Switch to a remembered account."""
        users_by_id = {user.uuid.hex: user for user in self.get_account_users()}
        selected_user = users_by_id.get(selected_account)
        if not selected_user:
            LOGGER.warning("selected account is not known", selected_account=selected_account)
            return self.executor.stage_invalid()
        if self.request.user.is_authenticated and selected_user.pk == self.request.user.pk:
            return self.executor.stage_ok()
        user_identifier = selected_user.email or selected_user.username
        if not self.is_oauth_authorization_plan():
            self.executor.plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = user_identifier
            return self.executor.stage_ok()
        return self.redirect_to_account_session(user_identifier, selected_user.uuid.hex)

    def challenge_valid(self, response: OAuthAccountSelectionChallengeResponse) -> HttpResponse:
        """Continue, switch to a remembered account, or use another account."""
        action = response.validated_data["action"]
        if action == "continue":
            return self.executor.stage_ok()
        if action == "login":
            return self.use_another_account()
        return self.switch_to_account(response.validated_data.get("selected_account", ""))
