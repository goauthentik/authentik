"""authentik email stage config"""
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template
from structlog.stdlib import get_logger

from authentik.blueprints.apps import ManagedAppConfig

LOGGER = get_logger()


class AuthentikStageEmailConfig(ManagedAppConfig):
    """authentik email stage config"""

    name = "authentik.stages.email"
    label = "authentik_stages_email"
    verbose_name = "authentik Stages.Email"
    default = True

    def reconcile_load_stages_emails_tasks(self):
        """Load stages.emails tasks"""
        self.import_module("authentik.stages.email.tasks")

    def reconcile_stage_templates_valid(self):
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
