"""id_token utils"""
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Optional, Union

from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
    from authentik.providers.oauth2.models import BaseGrantModel, OAuth2Provider


class SubModes(models.TextChoices):
    """Mode after which 'sub' attribute is generateed, for compatibility reasons"""

    HASHED_USER_ID = "hashed_user_id", _("Based on the Hashed User ID")
    USER_ID = "user_id", _("Based on user ID")
    USER_UUID = "user_uuid", _("Based on user UUID")
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


@dataclass(slots=True)
# pylint: disable=too-many-instance-attributes
class IDToken:
    """The primary extension that OpenID Connect makes to OAuth 2.0 to enable End-Users to be
    Authenticated is the ID Token data structure. The ID Token is a security token that contains
    Claims about the Authentication of an End-User by an Authorization Server when using a Client,
    and potentially other requested Claims. The ID Token is represented as a
    JSON Web Token (JWT) [JWT].

    https://openid.net/specs/openid-connect-core-1_0.html#IDToken"""

    # Issuer, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.1
    iss: Optional[str] = None
    # Subject, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.2
    sub: Optional[str] = None
    # Audience, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.3
    aud: Optional[Union[str, list[str]]] = None
    # Expiration time, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.4
    exp: Optional[int] = None
    # Issued at, https://www.rfc-editor.org/rfc/rfc7519.html#section-4.1.6
    iat: Optional[int] = None
    # Time when the authentication occurred,
    # https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    auth_time: Optional[int] = None
    # Authentication Context Class Reference,
    # https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    acr: Optional[str] = ACR_AUTHENTIK_DEFAULT
    # Authentication Methods References,
    # https://openid.net/specs/openid-connect-core-1_0.html#IDToken
    amr: Optional[list[str]] = None
    # Code hash value, http://openid.net/specs/openid-connect-core-1_0.html
    c_hash: Optional[str] = None
    # Value used to associate a Client session with an ID Token,
    # http://openid.net/specs/openid-connect-core-1_0.html
    nonce: Optional[str] = None
    # Access Token hash value, http://openid.net/specs/openid-connect-core-1_0.html
    at_hash: Optional[str] = None

    claims: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    # pylint: disable=too-many-locals
    def new(
        provider: "OAuth2Provider", token: "BaseGrantModel", request: HttpRequest, **kwargs
    ) -> "IDToken":
        """Create ID Token"""
        id_token = IDToken(provider, token, **kwargs)
        id_token.exp = int(token.expires.timestamp())
        id_token.iss = provider.get_issuer(request)
        id_token.aud = provider.client_id
        id_token.claims = {}

        if provider.sub_mode == SubModes.HASHED_USER_ID:
            id_token.sub = token.user.uid
        elif provider.sub_mode == SubModes.USER_ID:
            id_token.sub = str(token.user.pk)
        elif provider.sub_mode == SubModes.USER_UUID:
            id_token.sub = str(token.user.uuid)
        elif provider.sub_mode == SubModes.USER_EMAIL:
            id_token.sub = token.user.email
        elif provider.sub_mode == SubModes.USER_USERNAME:
            id_token.sub = token.user.username
        elif provider.sub_mode == SubModes.USER_UPN:
            id_token.sub = token.user.attributes.get("upn", token.user.uid)
        else:
            raise ValueError(
                f"Provider {provider} has invalid sub_mode selected: {provider.sub_mode}"
            )

        # Convert datetimes into timestamps.
        now = timezone.now()
        id_token.iat = int(now.timestamp())
        id_token.auth_time = int(token.auth_time.timestamp())

        # We use the timestamp of the user's last successful login (EventAction.LOGIN) for auth_time
        auth_event = get_login_event(request)
        if auth_event:
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
                id_token.amr = amr

        # Include (or not) user standard claims in the id_token.
        if provider.include_claims_in_id_token:
            from authentik.providers.oauth2.views.userinfo import UserInfoView

            user_info = UserInfoView()
            user_info.request = request
            id_token.claims = user_info.get_claims(token.provider, token)
        return id_token

    def to_dict(self) -> dict[str, Any]:
        """Convert dataclass to dict, and update with keys from `claims`"""
        id_dict = asdict(self)
        # All items without a value should be removed instead being set to None/null
        # https://openid.net/specs/openid-connect-core-1_0.html#JSONSerialization
        for key in list(id_dict.keys()):
            if id_dict[key] is None:
                id_dict.pop(key)
        id_dict.pop("claims")
        id_dict.update(self.claims)
        return id_dict

    def to_access_token(self, provider: "OAuth2Provider") -> str:
        """Encode id_token for use as access token, adding fields"""
        final = self.to_dict()
        final["azp"] = provider.client_id
        final["uid"] = generate_id()
        return provider.encode(final)

    def to_jwt(self, provider: "OAuth2Provider") -> str:
        """Shortcut to encode id_token to jwt, signed by self.provider"""
        return provider.encode(self.to_dict())
