"""OAuth2 Provider managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.providers.oauth2.models import ScopeMapping

SCOPE_OPENID_EXPRESSION = """
# This scope is required by the OpenID-spec, and must as such exist in authentik.
# The scope by itself does not grant any information
return {}
"""
SCOPE_EMAIL_EXPRESSION = """
return {
    "email": user.email,
    "email_verified": True
}
"""
SCOPE_PROFILE_EXPRESSION = """
return {
    # Because authentik only saves the user's full name, and has no concept of first and last names,
    # the full name is used as given name.
    # You can override this behaviour in custom mappings, i.e. `user.name.split(" ")`
    "name": user.name,
    "given_name": user.name,
    "family_name": "",
    "preferred_username": user.username,
    "nickname": user.username,
    # groups is not part of the official userinfo schema, but is a quasi-standard
    "groups": [group.name for group in user.ak_groups.all()],
}
"""


class ScopeMappingManager(ObjectManager):
    """OAuth2 Provider managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                ScopeMapping,
                "goauthentik.io/providers/oauth2/scope-openid",
                name="authentik default OAuth Mapping: OpenID 'openid'",
                scope_name="openid",
                expression=SCOPE_OPENID_EXPRESSION,
            ),
            EnsureExists(
                ScopeMapping,
                "goauthentik.io/providers/oauth2/scope-email",
                name="authentik default OAuth Mapping: OpenID 'email'",
                scope_name="email",
                description="Email address",
                expression=SCOPE_EMAIL_EXPRESSION,
            ),
            EnsureExists(
                ScopeMapping,
                "goauthentik.io/providers/oauth2/scope-profile",
                name="authentik default OAuth Mapping: OpenID 'profile'",
                scope_name="profile",
                description="General Profile Information",
                expression=SCOPE_PROFILE_EXPRESSION,
            ),
        ]
