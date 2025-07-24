"""AzureAD OAuth2 Views"""

from authentik.sources.oauth.types.entra_id import EntraIDType
from authentik.sources.oauth.types.registry import registry

# TODO: When removing this, add a migration for OAuthSource that sets
# provider_type to `entraid` if it is currently `azuread`


@registry.register()
class AzureADType(EntraIDType):
    """Azure AD Type definition"""

    verbose_name = "Azure AD"
    name = "azuread"

    urls_customizable = True
