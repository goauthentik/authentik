"""Enterprise app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseSearchConfig(EnterpriseConfig):
    """Enterprise app config"""

    name = "authentik.enterprise.search"
    label = "authentik_search"
    verbose_name = "authentik Enterprise.Search"
    default = True
