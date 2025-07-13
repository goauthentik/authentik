from rest_framework.test import APITestCase

from authentik.providers.scim.clients.schema import PatchOp, PatchOperation
from authentik.sources.scim.constants import SCIM_URN_USER_ENTERPRISE
from authentik.sources.scim.patch.parser import SCIMPathParser
from authentik.sources.scim.patch.processor import SCIMPatchProcessor


class TestSCIMPatchProcessor(APITestCase):

    def test_data(self):
        user_data = {
            "id": "user123",
            "userName": "john.doe",
            "name": {"formatted": "John Doe", "familyName": "Doe", "givenName": "John"},
            "emails": [
                {"value": "john.doe@example.com", "type": "work", "primary": True},
                {"value": "john.personal@example.com", "type": "personal", "primary": False},
            ],
            "phoneNumbers": [
                {"value": "+1-555-123-4567", "type": "work", "primary": True},
                {"value": "+1-555-987-6543", "type": "mobile", "primary": False},
            ],
            "addresses": [
                {
                    "streetAddress": "123 Work St",
                    "city": "Work City",
                    "type": "work",
                    "primary": True,
                },
                {
                    "streetAddress": "456 Home Ave",
                    "city": "Home City",
                    "type": "home",
                    "primary": False,
                },
                {
                    "streetAddress": "789 Other Rd",
                    "city": "Other City",
                    "type": "work",
                    "primary": False,
                },
            ],
        }

        # Create processor
        processor = SCIMPatchProcessor()

        # Example patch operations
        patches = [
            # Replace primary phone number
            PatchOperation(
                op=PatchOp.replace,
                path="phoneNumbers[primary eq true].value",
                value="+1-555-999-0000",
            ),
            # Add new email
            PatchOperation(
                op=PatchOp.add,
                path="emails",
                value={"value": "john.new@example.com", "type": "home", "primary": False},
            ),
            # Update user's given name
            PatchOperation(op=PatchOp.replace, path="name.givenName", value="Johnny"),
            # Remove work email
            PatchOperation(op=PatchOp.remove, path='emails[type eq "work"]'),
            # Add with empty path, simple object
            PatchOperation(op=PatchOp.add, path=None, value={"foo": "bar"}),
            # Empty path with complex object
            PatchOperation(op=PatchOp.add, path=None, value={"name.formatted": "formatted"}),
        ]
        result = processor.apply_patches(user_data, patches)
        self.assertEqual(
            result,
            {
                "id": "user123",
                "userName": "john.doe",
                "name": {"formatted": "formatted", "familyName": "Doe", "givenName": "Johnny"},
                "emails": [
                    {"value": "john.personal@example.com", "type": "personal", "primary": False},
                    {"value": "john.new@example.com", "type": "home", "primary": False},
                ],
                "phoneNumbers": [
                    {"value": "+1-555-999-0000", "type": "work", "primary": True},
                    {"value": "+1-555-987-6543", "type": "mobile", "primary": False},
                ],
                "addresses": [
                    {
                        "streetAddress": "123 Work St",
                        "city": "Work City",
                        "type": "work",
                        "primary": True,
                    },
                    {
                        "streetAddress": "456 Home Ave",
                        "city": "Home City",
                        "type": "home",
                        "primary": False,
                    },
                    {
                        "streetAddress": "789 Other Rd",
                        "city": "Other City",
                        "type": "work",
                        "primary": False,
                    },
                ],
                "foo": "bar",
            },
        )

    def test_parse(self):
        test_paths = [
            {
                "filter": "userName",
                "components": [{"attribute": "userName", "filter": None, "sub_attribute": None}],
            },
            {
                "filter": "name.givenName",
                "components": [{"attribute": "name", "filter": None, "sub_attribute": "givenName"}],
            },
            {
                "filter": "emails[primary eq true].value",
                "components": [
                    {
                        "attribute": "emails",
                        "filter": {
                            "type": "comparison",
                            "attribute": "primary",
                            "operator": "eq",
                            "value": True,
                        },
                        "sub_attribute": "value",
                    }
                ],
            },
            {
                "filter": 'phoneNumbers[type eq "work"].value',
                "components": [
                    {
                        "attribute": "phoneNumbers",
                        "filter": {
                            "type": "comparison",
                            "attribute": "type",
                            "operator": "eq",
                            "value": "work",
                        },
                        "sub_attribute": "value",
                    }
                ],
            },
            {
                "filter": 'addresses[type eq "work" and primary eq true].streetAddress',
                "components": [
                    {
                        "attribute": "addresses",
                        "filter": {
                            "type": "logical",
                            "operator": "and",
                            "left": {
                                "type": "comparison",
                                "attribute": "type",
                                "operator": "eq",
                                "value": "work",
                            },
                            "right": {
                                "type": "comparison",
                                "attribute": "primary",
                                "operator": "eq",
                                "value": True,
                            },
                        },
                        "sub_attribute": "streetAddress",
                    }
                ],
            },
            {
                "filter": f"{SCIM_URN_USER_ENTERPRISE}:manager",
                "components": [
                    {
                        "attribute": SCIM_URN_USER_ENTERPRISE,
                        "filter": None,
                        "sub_attribute": "manager",
                    }
                ],
            },
        ]

        for path in test_paths:
            with self.subTest(path=path["filter"]):
                parser = SCIMPathParser()
                components = parser.parse_path(path["filter"])
                self.assertEqual(components, path["components"])
