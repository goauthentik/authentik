"""SAML Source tests"""

from base64 import b64encode

from defusedxml.lxml import fromstring
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from authentik.common.saml.constants import NS_SAML_ASSERTION
from authentik.common.tests import dummy_get_response, load_fixture
from authentik.core.tests.utils import create_test_flow
from authentik.crypto.generators import generate_id
from authentik.sources.saml.models import SAMLSource, SAMLSourcePropertyMapping
from authentik.sources.saml.processors.response import ResponseProcessor

ROOT = fromstring(load_fixture("fixtures/response_success.xml").encode())
ROOT_GROUPS = fromstring(load_fixture("fixtures/response_success_groups.xml").encode())
NAME_ID = (
    ROOT.find(f"{{{NS_SAML_ASSERTION}}}Assertion")
    .find(f"{{{NS_SAML_ASSERTION}}}Subject")
    .find(f"{{{NS_SAML_ASSERTION}}}NameID")
)


class TestPropertyMappings(TestCase):
    """Test Property Mappings"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def test_user_base_properties(self):
        """Test user base properties"""
        properties = self.source.get_base_user_properties(root=ROOT, name_id=NAME_ID)
        self.assertEqual(
            properties,
            {
                "email": "foo@bar.baz",
                "name": "foo",
                "sn": "bar",
                "username": "jens@goauthentik.io",
            },
        )

    def test_group_base_properties(self):
        """Test group base properties"""
        properties = self.source.get_base_user_properties(root=ROOT_GROUPS, name_id=NAME_ID)
        self.assertEqual(properties["groups"], ["group 1", "group 2"])
        for group_id in ["group 1", "group 2"]:
            properties = self.source.get_base_group_properties(root=ROOT, group_id=group_id)
            self.assertEqual(properties, {"name": group_id})

    def test_user_property_mappings(self):
        """Test user property mappings"""
        self.source.user_property_mappings.add(
            SAMLSourcePropertyMapping.objects.create(
                name="test",
                expression="return {'attributes': {'department': 'Engineering'}, 'sn': None}",
            )
        )
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.user_properties,
            {
                "email": "foo@bar.baz",
                "name": "foo",
                "username": "jens@goauthentik.io",
                "attributes": {
                    "department": "Engineering",
                },
                "path": self.source.get_user_path(),
            },
        )

    def test_group_property_mappings(self):
        """Test group property mappings"""
        self.source.group_property_mappings.add(
            SAMLSourcePropertyMapping.objects.create(
                name="test",
                expression="return {'attributes': {'id': group_id}}",
            )
        )
        request = self.factory.post(
            "/",
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success_groups.xml").encode()
                ).decode()
            },
        )

        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(request)
        request.session.save()

        parser = ResponseProcessor(self.source, request)
        parser.parse()
        sfm = parser.prepare_flow_manager()
        self.assertEqual(
            sfm.groups_properties,
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
