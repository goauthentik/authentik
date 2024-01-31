"""authentik prompt stage app config"""

from django.apps import AppConfig


class AuthentikStagePromptConfig(AppConfig):
    """authentik prompt stage config"""

    name = "authentik.stages.prompt"
    label = "authentik_stages_prompt"
    verbose_name = "authentik Stages.Prompt"
