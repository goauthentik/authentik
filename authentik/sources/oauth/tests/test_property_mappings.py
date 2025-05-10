"""Apple Type tests"""

from copy import deepcopy

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from authentik.crypto.generators import generate_id
from authentik.lib.tests.utils import get_request
from authentik.sources.oauth.models import OAuthSource, OAuthSourcePropertyMapping
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager

INFO = {
    "sub": "83692",
    "name": "Alice Adams",
    "email": "alice@example.com",
    "department": "Engineering",
    "birthdate": "1975-12-31",
    "nickname": "foo",
}
IDENTIFIER = INFO["sub"]


class TestPropertyMappings(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="",
            consumer_key=generate_id(),
        )

    def test_user_base_properties(self):
        """Test user base properties"""
        properties = self.source.get_base_user_properties(info=INFO)
        self.assertEqual(
            properties,
            {
                "email": "alice@example.com",
                "groups": [],
                "name": "Alice Adams",
                "username": "foo",
            },
        )

    def test_group_base_properties(self):
        """Test group base properties"""
        info = deepcopy(INFO)
        info["groups"] = ["group 1", "group 2"]
        properties = self.source.get_base_user_properties(info=info)
        self.assertEqual(properties["groups"], ["group 1", "group 2"])
        for group_id in info["groups"]:
            properties = self.source.get_base_group_properties(info=info, group_id=group_id)
            self.assertEqual(properties, {"name": group_id})

    def test_user_property_mappings(self):
        self.source.user_property_mappings.add(
            OAuthSourcePropertyMapping.objects.create(
                name="test",
                expression="return {'attributes': {'department': info.get('department')}}",
            )
        )
        request = get_request("/", user=AnonymousUser())
        flow_manager = OAuthSourceFlowManager(self.source, request, IDENTIFIER, {"info": INFO}, {})
        self.assertEqual(
            flow_manager.user_properties,
            {
                "attributes": {
                    "department": "Engineering",
                },
                "email": "alice@example.com",
                "name": "Alice Adams",
                "username": "foo",
                "path": self.source.get_user_path(),
            },
        )

    def test_grup_property_mappings(self):
        info = deepcopy(INFO)
        info["groups"] = ["group 1", "group 2"]
        self.source.group_property_mappings.add(
            OAuthSourcePropertyMapping.objects.create(
                name="test",
                expression="return {'attributes': {'id': group_id}}",
            )
        )
        request = get_request("/", user=AnonymousUser())
        flow_manager = OAuthSourceFlowManager(self.source, request, IDENTIFIER, {"info": info}, {})
        self.assertEqual(
            flow_manager.groups_properties,
            {
                "group 1": {
                    "name": "group 1",
                    "attributes": {
                        "id": "group 1",
                    },
                },
                "group 2": {
                    "name": "group 2",
                    "attributes": {
                        "id": "group 2",
                    },
                },
            },
        )
