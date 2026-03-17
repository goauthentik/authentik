from authentik.enterprise.apps import EnterpriseConfig


class LifecycleConfig(EnterpriseConfig):
    name = "authentik.enterprise.lifecycle"
    label = "authentik_lifecycle"
    verbose_name = "authentik Enterprise.Lifecycle"
    default = True
