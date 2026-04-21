from os import getenv

from django_dramatiq_postgres.management.commands.worker import Command as BaseCommand

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.core.apps import Setup
from authentik.tenants.models import Tenant

BOOTSTRAP_BLUEPRINT = "system/bootstrap.yaml"


class Command(BaseCommand):

    def apply_bootstrap_blueprint(self):
        # If we have bootstrap credentials set, run bootstrap tasks outside of main server
        # sync, so that we can sure the first start actually has working bootstrap
        # credentials
        for tenant in Tenant.objects.filter(ready=True):
            with tenant:
                content = BlueprintInstance(path=BOOTSTRAP_BLUEPRINT).retrieve()
                importer = Importer.from_string(content)
                valid, logs = importer.validate()
                if not valid:
                    self.stderr.write("Blueprint invalid")
                    for log in logs:
                        self.stderr.write(f"\t{log.logger}: {log.event}: {log.attributes}")
                importer.apply()
                tenant.flags[Setup().key] = True
                tenant.save()

    def handle(self, pid_file, watch, verbosity, **options):
        if getenv("AUTHENTIK_BOOTSTRAP_PASSWORD") or getenv("AUTHENTIK_BOOTSTRAP_TOKEN"):
            self.apply_bootstrap_blueprint()
        return super().handle(pid_file, watch, verbosity, **options)
