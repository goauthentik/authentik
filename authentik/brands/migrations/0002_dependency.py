from django.db import migrations


class Migration(migrations.Migration):
    """
    Noop migration to make sure that data has been migrated from the old tenant system to this before changing this table any further.
    """

    dependencies = [
        ("authentik_brands", "0001_initial"),
        ("authentik_tenants", "0005_tenant_to_brand"),
    ]

    operations = []
