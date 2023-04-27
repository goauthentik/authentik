"""Send a test-email with global settings"""
from uuid import uuid4

from django.core.management.base import BaseCommand, no_translations

from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mail
from authentik.stages.email.utils import TemplateEmailMessage


class Command(BaseCommand):
    """Send a test-email with global settings"""

    @no_translations
    def handle(self, *args, **options):
        """Send a test-email with global settings"""
        delete_stage = False
        if options["stage"]:
            stages = EmailStage.objects.filter(name=options["stage"])
            if not stages.exists():
                self.stderr.write(f"Stage '{options['stage']}' does not exist")
                return
            stage = stages.first()
        else:
            stage = EmailStage.objects.create(
                name=f"temp-global-stage-{uuid4()}", use_global_settings=True
            )
            delete_stage = True
        message = TemplateEmailMessage(
            subject="authentik Test-Email",
            to=[options["to"]],
            template_name="email/setup.html",
            template_context={},
        )
        try:
            send_mail(message.__dict__, stage.pk)
        finally:
            if delete_stage:
                stage.delete()

    def add_arguments(self, parser):
        parser.add_argument("to", type=str)
        parser.add_argument("-s", "--stage", type=str)
