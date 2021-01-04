"""authentik email stage config"""
from importlib import import_module

from django.apps import AppConfig
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from structlog.stdlib import get_logger

LOGGER = get_logger()


class AuthentikStageEmailConfig(AppConfig):
    """authentik email stage config"""

    name = "authentik.stages.email"
    label = "authentik_stages_email"
    verbose_name = "authentik Stages.Email"

    def ready(self):
        from authentik.stages.email.models import EmailStage, EmailTemplates
        from authentik.events.models import Event, EventAction

        import_module("authentik.stages.email.tasks")
        for stage in EmailStage.objects.all():
            try:
                get_template(stage.template)
            except TemplateDoesNotExist:
                LOGGER.warning(
                    "Stage template does not exist, resetting", path=stage.template
                )
                Event.new(
                    EventAction.CONFIGURATION_ERROR,
                    stage=stage,
                    message=(
                        f"Template {stage.template} does not exist, resetting to default."
                        f" (Stage {stage.name})"
                    ),
                ).save()
                stage.template = EmailTemplates.ACCOUNT_CONFIRM
                stage.save()
