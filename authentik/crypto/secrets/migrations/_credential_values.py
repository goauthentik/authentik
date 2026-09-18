"""Move credential columns to secrets using historical models."""

from base64 import b64decode
from json import dumps

from yaml import safe_load


def migrate_credentials(apps, schema_editor, app_label, model_name, fields, *, include_empty=False):
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
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                value = dumps(value)
            if not value and not include_empty:
                continue
            base = f"{instance.name} {label}"
            name, suffix = base, 2
            while name in names:
                name = f"{base} ({suffix})"
                suffix += 1
            names.add(name)
            secret = Secret.objects.using(alias).create(
                name=name,
                type=secret_type or "text",
                value=value,
            )
            setattr(instance, new, secret)
            updated_fields.append(new)
        if updated_fields:
            instance.save(update_fields=updated_fields)


def restore_credentials(apps, schema_editor, app_label, model_name, fields):
    Model = apps.get_model(app_label, model_name)
    for instance in (
        Model.objects.using(schema_editor.connection.alias)
        .select_related(*(new for _, new, _, _ in fields))
        .iterator()
    ):
        for old, new, _, _ in fields:
            secret = getattr(instance, new)
            value = secret.value if secret else ""
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                if secret and secret.type == "file":
                    value = b64decode(value)
                value = safe_load(value) if value else {}
            setattr(instance, old, value)
        instance.save(update_fields=[old for old, _, _, _ in fields])
