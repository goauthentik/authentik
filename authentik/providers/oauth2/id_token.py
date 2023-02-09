"""id_token utils"""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from django.db import models
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from authentik.core.models import User
from authentik.events.signals import get_login_event
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.constants import (
    ACR_AUTHENTIK_DEFAULT,
    AMR_MFA,
    AMR_PASSWORD,
    AMR_WEBAUTHN,
)
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS

if TYPE_CHECKING:
    from authentik.providers.oauth2.models import OAuth2Provider


class SubModes(models.TextChoices):
    """Mode after which 'sub' attribute is generateed, for compatibility reasons"""

    HASHED_USER_ID = "hashed_user_id", _("Based on the Hashed User ID")
    USER_ID = "user_id", _("Based on user ID")
    USER_USERNAME = "user_username", _("Based on the username")
    USER_EMAIL = (
        "user_email",
        _("Based on the User's Email. This is recommended over the UPN method."),
    )
    USER_UPN = (
        "user_upn",
        _(
            "Based on the User's UPN, only works if user has a 'upn' attribute set. "
            "Use this method only if you have different UPN and Mail domains."
        ),
    )


@dataclass
class IDToken:
    """The primary extension that OpenID Connect makes to OAuth 2.0 to enable End-Users to be
    Authenticated is the ID Token data structure. The ID Token is a security token that contains
    Claims about the Authentication of an End-User by an Authorization Server when using a Client,
    and potentially other requested Claims. The ID Token is represented as a
    JSON Web Token (JWT) [JWT].

    https://openid.net/specs/openid-connect-core-1_0.html#IDToken"""

    _provider: "OAuth2Provider"
    _request: HttpRequest
    _user: User

    # Issuer, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.1
    iss: Optional[str] = None
    # Subject, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.2
    sub: Optional[str] = None
    # Audience, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.3
    aud: Optional[str] = None
    # Expiration time, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.4
    exp: Optional[int] = None
    # Issued at, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.6
    iat: Optional[int] = None
    # Time when the authentication occurred, https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    auth_time: Optional[int] = None
    # Authentication Context Class Reference, https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    acr: Optional[str] = ACR_AUTHENTIK_DEFAULT
    # Authentication Methods References, https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    amr: Optional[list[str]] = None
    # Code hash value, http://openid.net/specs/openid-connect-core-1_0.html
    c_hash: Optional[str] = None
    # Value used to associate a Client session with an ID Token, http://openid.net/specs/openid-connect-core-1_0.html
    nonce: Optional[str] = None
    # Access Token hash value, http://openid.net/specs/openid-connect-core-1_0.html
    at_hash: Optional[str] = None

    claims: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self, provider: "OAuth2Provider", user: User, request: HttpRequest, **kwargs
    ) -> None:
        sub = ""
        if provider.sub_mode == SubModes.HASHED_USER_ID:
            sub = user.uid
        elif provider.sub_mode == SubModes.USER_ID:
            sub = str(user.pk)
        elif provider.sub_mode == SubModes.USER_EMAIL:
            sub = user.email
        elif provider.sub_mode == SubModes.USER_USERNAME:
            sub = user.username
        elif provider.sub_mode == SubModes.USER_UPN:
            sub = user.attributes.get("upn", user.uid)
        else:
            raise ValueError(
                f"Provider {provider} has invalid sub_mode selected: {provider.sub_mode}"
            )
        # Convert datetimes into timestamps.
        now = datetime.now()
        iat_time = int(now.timestamp())

        super().__init__(
            _provider=provider,
            _user=user,
            _request=request,
            iss=provider.get_issuer(request),
            sub=sub,
            aud=provider.client_id,
            iat=iat_time,
            **kwargs,
        )

        # We use the timestamp of the user's last successful login (EventAction.LOGIN) for auth_time
        auth_event = get_login_event(request)
        if auth_event:
            auth_time = auth_event.created
            self.auth_time = int(auth_time.timestamp())
            # Also check which method was used for authentication
            method = auth_event.context.get(PLAN_CONTEXT_METHOD, "")
            method_args = auth_event.context.get(PLAN_CONTEXT_METHOD_ARGS, {})
            amr = []
            if method == "password":
                amr.append(AMR_PASSWORD)
            if method == "auth_webauthn_pwl":
                amr.append(AMR_WEBAUTHN)
            if "mfa_devices" in method_args:
                if len(amr) > 0:
                    amr.append(AMR_MFA)
            if amr:
                self.amr = amr

        # Include (or not) user standard claims in the id_token.
        if provider.include_claims_in_id_token:
            from authentik.providers.oauth2.views.userinfo import UserInfoView

            user_info = UserInfoView()
            user_info.request = request
            claims = user_info.get_claims(self)
            self.claims = claims

    def to_dict(self) -> dict[str, Any]:
        """Convert dataclass to dict, and update with keys from `claims`"""
        id_dict = asdict(self)
        for key, value in id_dict:
            if value is None:
                id_dict.pop(key)
        id_dict.pop("claims")
        id_dict.update(self.claims)
        return id_dict

    def to_access_token(self) -> str:
        """Encode id_token for use as access token, adding fields"""
        final = self.to_dict()
        final["azp"] = self._provider.client_id
        final["uid"] = generate_id()
        return self._provider.encode(final)

    def to_jwt(self) -> str:
        """Shortcut to encode id_token to jwt, signed by self.provider"""
        return self._provider.encode(self.to_dict())
