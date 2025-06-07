"""authentik prompt stage app config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikStagePromptConfig(ManagedAppConfig):
    """authentik prompt stage config"""

    name = "authentik.stages.prompt"
    label = "authentik_stages_prompt"
    verbose_name = "authentik Stages.Prompt"
    default = True
