from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id
from authentik.sources.scim.models import SCIMSource, SCIMSourceUser
from authentik.sources.scim.views.v2.patch import SCIMPatcher


class TestSCIMPatcher(APITestCase):

    def test_add(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Add", "path": "name.givenName", "value": "aqwer"},
                {"op": "Add", "path": "name.familyName", "value": "qwerqqqq"},
                {"op": "Add", "path": "name.formatted", "value": "aqwer qwerqqqq"},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        patcher = SCIMPatcher(connection, req["Operations"])
        updated = patcher.apply()
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                    "familyName": "qwerqqqq",
                    "formatted": "aqwer qwerqqqq",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )

    def test_add_no_path(self):
        """Test add patch with no path set"""
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Add", "value": {"externalId": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "displayName": "Test MS",
            },
        )
        patcher = SCIMPatcher(connection, req["Operations"])
        updated = patcher.apply()
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "aqwer",
                "displayName": "Test MS",
            },
        )

    def test_replace(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Replace", "path": "name", "value": {"givenName": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        patcher = SCIMPatcher(connection, req["Operations"])
        updated = patcher.apply()
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )

    def test_replace_no_path(self):
        """Test value replace with no path"""
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Replace", "value": {"externalId": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        patcher = SCIMPatcher(connection, req["Operations"])
        updated = patcher.apply()
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "aqwer",
                "displayName": "Test MS",
            },
        )

    def test_remove(self):
        req = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {"op": "Remove", "path": "name", "value": {"givenName": "aqwer"}},
            ],
        }
        user = create_test_user()
        source = SCIMSource.objects.create(slug=generate_id())
        connection = SCIMSourceUser.objects.create(
            user=user,
            id=generate_id(),
            source=source,
            attributes={
                "meta": {"resourceType": "User"},
                "active": True,
                "name": {
                    "givenName": "aqwer",
                },
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
        patcher = SCIMPatcher(connection, req["Operations"])
        updated = patcher.apply()
        self.assertEqual(
            updated,
            {
                "meta": {"resourceType": "User"},
                "active": True,
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User",
                    "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                ],
                "userName": "test@t.goauthentik.io",
                "externalId": "test",
                "displayName": "Test MS",
            },
        )
