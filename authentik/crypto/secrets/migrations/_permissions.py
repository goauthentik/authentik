"""Preserve existing credential access when credentials move to secrets."""

from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions


def preserve_permissions(apps, schema_editor, app_label, model_name, *, value_permission=None):
    """Grant access to the new secrets to everyone who could use their objects.

    Roles that can view or change an object get `view_secret` on its secrets, as
    object permissions, so no role gains access to unrelated secrets. Roles that
    could read the credential through the object's API, which is those with
    `<value_permission>_<model>`, also get `view_secret_value`. Initial
    permissions are extended the same way, so secrets created together with a new
    object stay visible to its creator.
    """
    alias = schema_editor.connection.alias
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    ObjectPermission = apps.get_model("guardian", "RoleObjectPermission")
    ModelPermission = apps.get_model("guardian", "RoleModelPermission")
    InitialPermissionsPermission = apps.get_model("authentik_rbac", "InitialPermissionsPermission")
    Secret = apps.get_model("authentik_crypto_secrets", "Secret")
    Model = apps.get_model(app_label, model_name)

    create_permissions(
        global_apps.get_app_config("authentik_crypto_secrets"), apps=apps, using=alias
    )
    secret_type = ContentType.objects.using(alias).get(
        app_label="authentik_crypto_secrets", model="secret"
    )
    secret_permissions = {
        permission.codename: permission
        for permission in Permission.objects.using(alias).filter(content_type=secret_type)
    }
    content_type = (
        ContentType.objects.using(alias).filter(app_label=app_label, model=model_name).first()
    )
    if not content_type:
        return
    secret_fields = [field.attname for field in Model._meta.fields if field.related_model is Secret]

    for action in ["view", "change"]:
        grants = [secret_permissions["view_secret"]]
        if action == value_permission:
            grants.append(secret_permissions["view_secret_value"])
        filters = {"content_type": content_type, "permission__codename": f"{action}_{model_name}"}

        for initial_permissions_id in (
            InitialPermissionsPermission.objects.using(alias)
            .filter(
                permission__content_type=content_type, permission__codename=f"{action}_{model_name}"
            )
            .values_list("initial_permissions_id", flat=True)
        ):
            InitialPermissionsPermission.objects.using(alias).bulk_create(
                [
                    InitialPermissionsPermission(
                        initial_permissions_id=initial_permissions_id, permission=grant
                    )
                    for grant in grants
                ],
                ignore_conflicts=True,
            )

        global_roles = set(
            ModelPermission.objects.using(alias).filter(**filters).values_list("role_id", flat=True)
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
                        permission=grant,
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
