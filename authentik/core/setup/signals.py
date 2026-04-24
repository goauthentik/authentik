from os import getenv

from django.dispatch import receiver
from structlog.stdlib import get_logger

from authentik.blueprints.models import BlueprintInstance
from authentik.blueprints.v1.importer import Importer
from authentik.core.apps import Setup
from authentik.root.signals import post_startup
from authentik.tenants.models import Tenant

BOOTSTRAP_BLUEPRINT = "system/bootstrap.yaml"

LOGGER = get_logger()


@receiver(post_startup)
def post_startup_setup_bootstrap(sender, **_):
    if not getenv("AUTHENTIK_BOOTSTRAP_PASSWORD") and not getenv("AUTHENTIK_BOOTSTRAP_TOKEN"):
        return
    LOGGER.info("Configuring authentik through bootstrap environment variables")
    content = BlueprintInstance(path=BOOTSTRAP_BLUEPRINT).retrieve()
    # If we have bootstrap credentials set, run bootstrap tasks outside of main server
    # sync, so that we can sure the first start actually has working bootstrap
    # credentials
    for tenant in Tenant.objects.filter(ready=True):
        if Setup.get(tenant=tenant):
            LOGGER.info("Tenant is already setup, skipping", tenant=tenant.schema_name)
            continue
        with tenant:
            importer = Importer.from_string(content)
            valid, logs = importer.validate()
            if not valid:
                LOGGER.warning("Blueprint invalid", tenant=tenant.schema_name)
                for log in logs:
                    log.log()
            importer.apply()
            Setup.set(True, tenant=tenant)
