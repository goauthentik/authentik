"""authentik email stage config"""
from importlib import import_module

from django.apps import AppConfig
from django.db import ProgrammingError
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
        import_module("authentik.stages.email.tasks")
        try:
            self.validate_stage_templates()
        except ProgrammingError:
            pass

    def validate_stage_templates(self):
        """Ensure all stage's templates actually exist"""
        from authentik.events.models import Event, EventAction
        from authentik.stages.email.models import EmailStage, EmailTemplates

        for stage in EmailStage.objects.all():
            try:
                get_template(stage.template)
            except TemplateDoesNotExist:
                LOGGER.warning("Stage template does not exist, resetting", path=stage.template)
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
