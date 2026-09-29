"""Send a test-email with global settings"""

from django.core.management.base import no_translations

from authentik.lib.utils.reflection import class_to_path
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import send_mail
from authentik.stages.email.utils import TemplateEmailMessage
from authentik.tenants.management import TenantCommand


class Command(TenantCommand):
    """Send a test-email with global settings"""

    @no_translations
    def handle_per_tenant(self, *args, **options):
        """Send a test-email with global settings"""
        stage = None
        if options["stage"]:
            stages = EmailStage.objects.filter(name=options["stage"])
            if not stages.exists():
                self.stderr.write(f"Stage '{options['stage']}' does not exist")
                return
            stage = stages.first()
        message = TemplateEmailMessage(
            subject="authentik Test-Email",
            to=[("", options["to"])],
            template_name="email/setup.html",
            template_context={},
        )
        # Use the class path instead of the class itself for serialization
        stage_class_path, stage_pk = None, None
        if stage:
            stage_class_path = class_to_path(stage.__class__)
            stage_pk = str(stage.pk)
        send_mail.send(message.__dict__, stage_class_path, stage_pk).get_result(block=True)

        self.stdout.write(self.style.SUCCESS(f"Test email sent to {options['to']}"))

    def add_arguments(self, parser):
        parser.add_argument("to", type=str)
        parser.add_argument("-S", "--stage", type=str)
