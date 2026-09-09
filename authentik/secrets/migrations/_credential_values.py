"""Move credential columns to secrets using historical models."""

from base64 import b64decode
from json import dumps

from yaml import safe_load


def migrate_credentials(apps, schema_editor, app_label, model_name, fields):
    alias = schema_editor.connection.alias
    Model = apps.get_model(app_label, model_name)
    Secret = apps.get_model("authentik_secrets", "Secret")
    names = set(Secret.objects.using(alias).values_list("name", flat=True))
    for instance in Model.objects.using(alias).iterator():
        for old, new, secret_type in fields:
            value = getattr(instance, old)
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                value = dumps(value)
            if not value:
                continue
            base = f"{instance.name} {old.replace('_', ' ')}"
            name, suffix = base, 2
            while name in names:
                name = f"{base} ({suffix})"
                suffix += 1
            names.add(name)
            secret = Secret.objects.using(alias).create(name=name, type=secret_type, value=value)
            setattr(instance, new, secret)
            instance.save(update_fields=[new])


def restore_credentials(apps, schema_editor, app_label, model_name, fields):
    Model = apps.get_model(app_label, model_name)
    for instance in (
        Model.objects.using(schema_editor.connection.alias)
        .select_related(*(new for _, new, _ in fields))
        .iterator()
    ):
        for old, new, _ in fields:
            secret = getattr(instance, new)
            value = secret.value if secret else ""
            if Model._meta.get_field(old).get_internal_type() == "JSONField":
                if secret and secret.type == "file":
                    value = b64decode(value)
                value = safe_load(value) if value else {}
            setattr(instance, old, value)
        instance.save(update_fields=[old for old, _, _ in fields])
