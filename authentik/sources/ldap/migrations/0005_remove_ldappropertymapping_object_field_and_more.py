# Generated by Django 5.0.2 on 2024-02-29 11:21

import textwrap

from django.db import migrations


def migrate_ldap_property_mappings_object_field(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    LDAPPropertyMapping = apps.get_model("authentik_sources_ldap", "LDAPPropertyMapping")
    for mapping in LDAPPropertyMapping.objects.all():
        mapping.expression = f"""
# This property mapping has been automatically changed to
# match the new semantics of source property mappings.
# You can simplify it if you want.
# You should return a dictionary of fields to set on the user or the group.
# For instance:
# return {{
#     "{mapping.object_field}": ldap.get("{mapping.object_field}")
# }}
# Note that this example has been generated and should not be used as-is.
def get_field():
    {textwrap.indent(mapping.expression, prefix='    ')}

field = "{mapping.object_field}"
result = {{"attributes": {{}}}}
if field.startswith("attributes."):
    # Adapted from authentik/lib/config.py::set_path_in_dict
    root = result
    path_parts = field.split(".")
    for comp in path_parts[:-1]
        if comp not in root:
            root[comp] = {{}}
        root = root.get(comp, {{}})
    root[path_parts[-1]] = get_field()
else:
    result[field] = get_field()
return result
        """
        mapping.save()


def migrate_ldap_property_mappings_to_new_fields(apps, schema_editor):
    if schema_editor.connection.alias != "default":
        return
    LDAPSource = apps.get_model("authentik_sources_ldap", "LDAPSource")
    for source in LDAPSource.objects.all():
        source.user_property_mappings.set(source.property_mappings)
        source.group_property_mappings.set(source.property_mappings_group)


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_sources_ldap", "0004_ldapsource_password_login_update_internal_password"),
        ("authentik_core", "0036_source_group_property_mappings_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_ldap_property_mappings_object_field),
        migrations.RunPython(migrate_ldap_property_mappings_to_new_fields),
        migrations.RemoveField(
            model_name="ldappropertymapping",
            name="object_field",
        ),
        migrations.RemoveField(
            model_name="ldapsource",
            name="property_mappings_group",
        ),
    ]