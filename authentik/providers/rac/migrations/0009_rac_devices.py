# Move RAC endpoints into the endpoint device inventory

import django.db.models.deletion
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def migrate_endpoints_to_devices(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    """Convert every RAC endpoint into a device.

    The device re-uses the endpoint's primary key as its `device_uuid`, and the
    endpoint's host and protocol become a connection override for the device."""
    db_alias = schema_editor.connection.alias
    Endpoint = apps.get_model("authentik_providers_rac", "Endpoint")
    ConnectionToken = apps.get_model("authentik_providers_rac", "ConnectionToken")
    RACConnectionOverride = apps.get_model("authentik_providers_rac", "RACConnectionOverride")
    Device = apps.get_model("authentik_endpoints", "Device")
    PolicyBinding = apps.get_model("authentik_policies", "PolicyBinding")

    # Connection tokens are bound to a single browser session and are re-created on the
    # next launch, so they're dropped instead of migrated.
    ConnectionToken.objects.using(db_alias).all().delete()

    # Device names are unique, endpoint names are not
    taken_names = set(Device.objects.using(db_alias).values_list("name", flat=True))

    def unique_name(endpoint) -> str:
        name = endpoint.name
        if name in taken_names:
            name = f"{endpoint.name} ({endpoint.provider.name})"
        base = name
        suffix = 2
        while name in taken_names:
            name = f"{base} {suffix}"
            suffix += 1
        taken_names.add(name)
        return name

    for endpoint in Endpoint.objects.using(db_alias).select_related("provider").iterator():
        device = Device.objects.using(db_alias).create(
            device_uuid=endpoint.pk,
            name=unique_name(endpoint),
            identifier=f"rac://{endpoint.pk}",
            expiring=False,
            policy_engine_mode=endpoint.policy_engine_mode,
        )
        RACConnectionOverride.objects.using(db_alias).create(
            device=device,
            host=endpoint.host,
            protocol=endpoint.protocol,
        )
        # Policies bound to the endpoint now apply to the device
        PolicyBinding.objects.using(db_alias).filter(target_id=endpoint.pk).update(
            target_id=device.pbm_uuid
        )

    # Deleting the endpoints also removes their policy binding model rows
    Endpoint.objects.using(db_alias).all().delete()


def remove_endpoint_permissions(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    """Remove permissions (and object-level permissions) of the removed models"""
    db_alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.using(db_alias).filter(
        app_label="authentik_providers_rac",
        model__in=["endpoint", "endpointpropertymapping"],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_endpoints", "0005_alter_deviceuserbinding_managers"),
        ("authentik_policies", "0011_policybinding_failure_result_and_more"),
        ("authentik_providers_rac", "0008_endpointpropertymapping_and_more"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="racprovider",
            name="maximum_connections",
            field=models.IntegerField(
                default=1,
                help_text=(
                    "Maximum concurrent connections to a single device. Can be set to -1 to "
                    "disable the limit."
                ),
            ),
        ),
        migrations.AddField(
            model_name="racprovider",
            name="access_group",
            field=models.ForeignKey(
                blank=True,
                default=None,
                help_text=(
                    "Only devices in this access group can be accessed through this provider. "
                    "When left empty, every device the user has access to can be accessed."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                to="authentik_endpoints.deviceaccessgroup",
            ),
        ),
        migrations.CreateModel(
            name="RACConnectionOverride",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "host",
                    models.TextField(
                        help_text="Hostname/IP to connect to. Optionally specify the port."
                    ),
                ),
                (
                    "protocol",
                    models.TextField(choices=[("rdp", "Rdp"), ("vnc", "Vnc"), ("ssh", "Ssh")]),
                ),
                (
                    "device",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rac_override",
                        to="authentik_endpoints.device",
                    ),
                ),
            ],
            options={
                "verbose_name": "RAC Connection override",
                "verbose_name_plural": "RAC Connection overrides",
            },
        ),
        migrations.RunPython(migrate_endpoints_to_devices, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="connectiontoken",
            name="endpoint",
        ),
        migrations.AddField(
            model_name="connectiontoken",
            name="protocol",
            # All connection tokens are deleted above, so the column can be added as
            # non-nullable without a default
            field=models.TextField(choices=[("rdp", "Rdp"), ("vnc", "Vnc"), ("ssh", "Ssh")]),
        ),
        migrations.AddField(
            model_name="connectiontoken",
            name="device",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="authentik_endpoints.device",
            ),
        ),
        migrations.RemoveField(
            model_name="endpointpropertymapping",
            name="endpoint",
        ),
        migrations.RemoveField(
            model_name="endpointpropertymapping",
            name="property_mapping",
        ),
        migrations.RemoveField(
            model_name="endpoint",
            name="property_mappings",
        ),
        migrations.RemoveField(
            model_name="endpoint",
            name="provider",
        ),
        migrations.DeleteModel(
            name="EndpointPropertyMapping",
        ),
        migrations.DeleteModel(
            name="Endpoint",
        ),
        migrations.RunPython(remove_endpoint_permissions, migrations.RunPython.noop),
    ]
