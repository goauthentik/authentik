"""Test Source Property mappings"""

from django.test import TestCase

from authentik.core.models import Group, PropertyMapping, Source, User
from authentik.core.sources.mapper import SourceMapper
from authentik.crypto.generators import generate_id


class ProxySource(Source):
    @property
    def property_mapping_type(self):
        return PropertyMapping

    def get_base_user_properties(self, **kwargs):
        return {
            "username": kwargs.get("username", None),
            "email": kwargs.get("email", "default@authentik"),
        }

    def get_base_group_properties(self, **kwargs):
        return {"name": kwargs.get("name", None)}

    class Meta:
        proxy = True


class TestSourcePropertyMappings(TestCase):
    """Test Source PropertyMappings"""

    def test_base_properties(self):
        source = ProxySource.objects.create(name=generate_id(), slug=generate_id(), enabled=True)
        mapper = SourceMapper(source)

        user_base_properties = mapper.get_base_properties(User, username="test1")
        self.assertEqual(
            user_base_properties,
            {
                "username": "test1",
                "email": "default@authentik",
                "path": f"goauthentik.io/sources/{source.slug}",
            },
        )

        group_base_properties = mapper.get_base_properties(Group)
        self.assertEqual(group_base_properties, {"name": None})

    def test_build_properties(self):
        source = ProxySource.objects.create(name=generate_id(), slug=generate_id(), enabled=True)
        mapper = SourceMapper(source)

        source.user_property_mappings.add(
            PropertyMapping.objects.create(
                name=generate_id(),
                expression="""
                    return {"username": data.get("username", None), "email": None}
                """,
            )
        )

        properties = mapper.build_object_properties(
            object_type=User, user=None, request=None, username="test1", data={"username": "test2"}
        )

        self.assertEqual(
            properties,
            {
                "username": "test2",
                "path": f"goauthentik.io/sources/{source.slug}",
                "attributes": {},
            },
        )
