"""Preserve existing credential visibility when creating secret references."""

from django.apps import apps as real_apps
from django.contrib.auth.management import create_permissions

# Match the credential visibility in the consumer serializers before this migration.
# All other migrated credentials were write-only.
VALUE_PERMISSIONS = {
    "authentik_outposts.kubernetesserviceconnection": "change",
    "authentik_providers_google_workspace.googleworkspaceprovider": "change",
    "authentik_endpoints_connectors_google_chrome.googlechromeconnector": "change",
    "authentik_stages_authenticator_endpoint_gdtc.authenticatorendpointgdtcstage": "change",
    "authentik_providers_oauth2.oauth2provider": "change",
    "authentik_providers_radius.radiusprovider": "change",
    "authentik_sources_plex.plexsource": "change",
    "authentik_events.notificationtransport": "view",
}


def preserve_role_permissions(apps, schema_editor, consumers):
    """Copy consumer grants to their secrets without granting model-wide access."""
    alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    ObjectPermission = apps.get_model("guardian", "RoleObjectPermission")
    ModelPermission = apps.get_model("guardian", "RoleModelPermission")
    Secret = apps.get_model("authentik_crypto_secrets", "Secret")
    create_permissions(real_apps.get_app_config("authentik_crypto_secrets"), apps=apps, using=alias)
    secret_type = ContentType.objects.using(alias).get(
        app_label="authentik_crypto_secrets", model="secret"
    )
    permissions = {
        permission.codename: permission
        for permission in Permission.objects.using(alias).filter(content_type=secret_type)
    }
    for app_label, model_name in consumers:
        Model = apps.get_model(app_label, model_name)
        secret_fields = [
            field.attname for field in Model._meta.fields if field.related_model is Secret
        ]
        content_type = (
            ContentType.objects.using(alias).filter(app_label=app_label, model=model_name).first()
        )
        if not content_type:
            continue
        for action in ["view", "change"]:
            grants = {"view_secret"}
            if VALUE_PERMISSIONS.get(Model._meta.label_lower) == action:
                grants.add("view_secret_value")
            filters = {
                "content_type": content_type,
                "permission__codename": f"{action}_{model_name}",
            }
            global_roles = set(
                ModelPermission.objects.using(alias)
                .filter(**filters)
                .values_list("role_id", flat=True)
            )
            object_roles = {}
            for object_pk, role_id in (
                ObjectPermission.objects.using(alias)
                .filter(**filters)
                .values_list("object_pk", "role_id")
                .iterator()
            ):
                object_roles.setdefault(object_pk, set()).add(role_id)
            if not global_roles and not object_roles:
                continue
            for pk, *secret_ids in (
                Model.objects.using(alias).values_list("pk", *secret_fields).iterator()
            ):
                roles = global_roles | object_roles.get(str(pk), set())
                ObjectPermission.objects.using(alias).bulk_create(
                    [
                        ObjectPermission(
                            role_id=role_id,
                            permission=permissions[grant],
                            content_type=secret_type,
                            object_pk=str(secret_id),
                        )
                        for secret_id in set(secret_ids) - {None}
                        for role_id in roles
                        for grant in grants
                    ],
                    ignore_conflicts=True,
                    batch_size=1000,
                )
