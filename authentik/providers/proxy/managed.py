"""OAuth2 Provider managed objects"""
from authentik.blueprints.manager import EnsureExists, ObjectManager
from authentik.providers.oauth2.models import ScopeMapping
from authentik.providers.proxy.models import SCOPE_AK_PROXY

SCOPE_AK_PROXY_EXPRESSION = """
# This mapping is used by the authentik proxy. It passes extra user attributes,
# which are used for example for the HTTP-Basic Authentication mapping.
return {
    "ak_proxy": {
        "user_attributes": request.user.group_attributes(request),
        "is_superuser": request.user.is_superuser,
    }
}"""


class ProxyScopeMappingManager(ObjectManager):
    """OAuth2 Provider managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                ScopeMapping,
                "goauthentik.io/providers/proxy/scope-proxy",
                name="authentik default OAuth Mapping: Proxy outpost",
                scope_name=SCOPE_AK_PROXY,
                expression=SCOPE_AK_PROXY_EXPRESSION,
            ),
        ]
