"""authentik stage app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseStageSourceConfig(EnterpriseConfig):
    """authentik source stage config"""

    name = "authentik.enterprise.stages.source"
    label = "authentik_stages_source"
    verbose_name = "authentik Enterprise.Stages.Source"
    default = True
