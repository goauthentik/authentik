from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseRequestsConfig(EnterpriseConfig):
    name = "authentik.enterprise.requests"
    label = "authentik_requests"
    verbose_name = "authentik Enterprise.Requests"
    default = True
