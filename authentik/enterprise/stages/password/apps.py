"""authentik password stage app config."""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseStagePasswordConfig(EnterpriseConfig):
    """authentik password stage config."""

    name = "authentik.enterprise.stages.password"
    label = "authentik_enterprise_stages_password"
    verbose_name = "authentik Enterprise.Stages.Password"
    default = True
