from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def migrate_permissions_before_delete(apps: Apps, schema_editor: BaseDatabaseSchemaEditor):
    """
    Migrate permissions from OldAuthenticatedSession to AuthenticatedSession
    before the model is deleted.
    """
    db_alias = schema_editor.connection.alias
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")

    # Get the content types
    try:
        old_ct = ContentType.objects.using(db_alias).get(
            app_label="authentik_core",
            model="oldauthenticatedsession"
        )
        new_ct = ContentType.objects.using(db_alias).get(
            app_label="authentik_core",
            model="authenticatedsession"
        )
    except ContentType.DoesNotExist:
        return  # If either content type doesn't exist, nothing to migrate

    # Get all permissions for the old content type
    old_perms = Permission.objects.using(db_alias).filter(content_type=old_ct)

    # Create equivalent permissions for the new content type
    for old_perm in old_perms:
        new_codename = old_perm.codename.replace('oldauthenticatedsession', 'authenticatedsession')
        new_name = old_perm.name.replace('oldauthenticatedsession', 'authenticated session')

        new_perm, created = Permission.objects.using(db_alias).get_or_create(
            codename=new_codename,
            content_type=new_ct,
            defaults={'name': new_name}
        )

        # Update all groups and user permissions to point to the new permission
        if not created:
            # Update group permissions
            for group in Group.objects.using(db_alias).filter(permissions=old_perm):
                group.permissions.remove(old_perm)
                group.permissions.add(new_perm)

            # Update user permissions
            for user in old_perm.user_set.using(db_alias).all():
                user.user_permissions.remove(old_perm)
                user.user_permissions.add(new_perm)

    # The model deletion will handle removing the old permissions


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0001_initial'),
        ("authentik_core", "0046_session_and_more"),
        ("authentik_providers_rac", "0007_migrate_session"),
        ("authentik_providers_oauth2", "0028_migrate_session"),
    ]

    operations = [
        migrations.RunPython(
            code=migrate_permissions_before_delete,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.DeleteModel(
            name="OldAuthenticatedSession",
        ),
    ]
