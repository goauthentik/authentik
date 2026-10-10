"""Move credential columns to secrets using historical models."""

from json import JSONDecodeError, dumps, loads

from django.db import migrations
from yaml import safe_load

from authentik.crypto.secrets.migrations._permissions import preserve_permissions


def move_credentials(
    app_label, model_name, fields, *, include_empty=False, value_permission=None
) -> migrations.RunPython:
    """Move credential columns into secrets, and back when migrating backwards.

    See migrate_credentials for `fields` and `include_empty`, and preserve_permissions for
    `value_permission`.
    """

    def forwards(apps, schema_editor):
        migrate_credentials(
            apps, schema_editor, app_label, model_name, fields, include_empty=include_empty
        )
        preserve_permissions(
            apps, schema_editor, app_label, model_name.lower(), value_permission=value_permission
        )

    def backwards(apps, schema_editor):
        restore_credentials(apps, schema_editor, app_label, model_name, fields)

    return migrations.RunPython(forwards, backwards)


def migrate_credentials(apps, schema_editor, app_label, model_name, fields, *, include_empty=False):
    """Create a secret for each credential and reference it from its object.

    `fields` lists `(column, reference, type, label)` tuples. `type` is a secret type, or a
    callable that picks one for each row. Empty credentials stay without a secret unless
    `include_empty` is set.
    """
    alias = schema_editor.connection.alias
    Model = apps.get_model(app_label, model_name)
    Secret = apps.get_model("authentik_crypto_secrets", "Secret")
    names = set(Secret.objects.using(alias).values_list("name", flat=True))
    for instance in Model.objects.using(alias).iterator():
        updated_fields = []
        for old, new, secret_type, label in fields:
            if getattr(instance, f"{new}_id") is not None:
                continue
            value = getattr(instance, old)
            if not value and not include_empty:
                continue
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                value = dumps(value)
            base = f"{instance.name} {label}"
            name, suffix = base, 2
            while name in names:
                name = f"{base} ({suffix})"
                suffix += 1
            names.add(name)
            secret = Secret.objects.using(alias).create(
                name=name,
                type=secret_type(instance) if callable(secret_type) else secret_type,
                secret_value=value,
            )
            setattr(instance, new, secret)
            updated_fields.append(new)
        if updated_fields:
            instance.save(update_fields=updated_fields)
    # The updates above queue deferred foreign key checks on this table. Django adds the
    # reference's constraint and index at the end of the migration, and Postgres refuses to
    # ALTER a table with pending trigger events in the same transaction.
    schema_editor.execute("SET CONSTRAINTS ALL IMMEDIATE")


def restore_credentials(apps, schema_editor, app_label, model_name, fields):
    """Copy secret values back into the legacy columns."""
    Model = apps.get_model(app_label, model_name)
    for instance in (
        Model.objects.using(schema_editor.connection.alias)
        .select_related(*(new for _, new, _, _ in fields))
        .iterator()
    ):
        for old, new, _, _ in fields:
            secret = getattr(instance, new)
            value = secret.secret_value if secret else ""
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                # JSON secrets may be written in YAML syntax.
                try:
                    value = loads(value) if value else {}
                except JSONDecodeError:
                    value = safe_load(value)
            setattr(instance, old, value)
        instance.save(update_fields=[old for old, _, _, _ in fields])
