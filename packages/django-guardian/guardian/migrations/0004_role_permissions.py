import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("guardian", "0003_remove_groupobjectpermission_guardian_gr_content_ae6aec_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoleModelPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype"
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="auth.permission"
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="authentik_rbac.role"
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["permission", "role", "content_type"],
                        name="guardian_ro_permiss_eb3837_idx",
                    ),
                    models.Index(
                        fields=["role", "content_type"], name="guardian_ro_role_id_268ee1_idx"
                    ),
                ],
                "unique_together": {("role", "permission")},
            },
        ),
        migrations.CreateModel(
            name="RoleObjectPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("object_pk", models.CharField(max_length=255, verbose_name="object ID")),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype"
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="auth.permission"
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="authentik_rbac.role"
                    ),
                ),
            ],
            options={
                "abstract": False,
                "indexes": [
                    models.Index(
                        fields=["permission", "role", "content_type", "object_pk"],
                        name="guardian_ro_permiss_731f53_idx",
                    ),
                    models.Index(
                        fields=["role", "content_type", "object_pk"],
                        name="guardian_ro_role_id_82d58d_idx",
                    ),
                ],
                "unique_together": {("role", "permission", "object_pk")},
            },
        ),
    ]
