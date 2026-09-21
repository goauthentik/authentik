"""authentik account lockdown stage app config"""

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseStageAccountLockdownConfig(EnterpriseConfig):
    """authentik account lockdown stage config"""

    name = "authentik.enterprise.stages.account_lockdown"
    label = "authentik_stages_account_lockdown"
    verbose_name = "authentik Enterprise.Stages.Account Lockdown"
    default = True
