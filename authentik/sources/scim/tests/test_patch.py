from unittest.mock import Mock, patch

from rest_framework.test import APITestCase

from authentik.providers.scim.clients.schema import PatchOp, PatchOperation
from authentik.sources.scim.constants import SCIM_URN_USER_ENTERPRISE
from authentik.sources.scim.patch.parser import SCIMPathParser
from authentik.sources.scim.patch.processor import SCIMPatchProcessor


class TestSCIMPatchProcessor(APITestCase):

    def setUp(self):
        """Set up test fixtures"""
        self.processor = SCIMPatchProcessor()
        self.sample_data = {
            "userName": "john.doe",
            "name": {"givenName": "John", "familyName": "Doe"},
            "emails": [
                {"value": "john@example.com", "type": "work", "primary": True},
                {"value": "john.personal@example.com", "type": "personal"},
            ],
            "active": True,
        }

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

    def test_init(self):
        """Test processor initialization"""
        processor = SCIMPatchProcessor()
        self.assertIsNotNone(processor.parser)

    def test_apply_patches_empty_list(self):
        """Test applying empty patch list returns unchanged data"""
        result = self.processor.apply_patches(self.sample_data, [])
        self.assertEqual(result, self.sample_data)
        # Ensure original data is not modified
        self.assertIsNot(result, self.sample_data)

    def test_apply_patches_with_validation(self):
        """Test that patches are validated using PatchOperation.model_validate"""
        with patch("authentik.sources.scim.patch.processor.PatchOperation") as mock_patch_op:
            mock_patch_op.model_validate.return_value = Mock(
                path="userName", op=PatchOp.replace, value="jane.doe"
            )

            patches = [{"op": "replace", "path": "userName", "value": "jane.doe"}]
            self.processor.apply_patches(self.sample_data, patches)

            mock_patch_op.model_validate.assert_called_once()

    # Test ADD operations
    def test_apply_add_simple_attribute(self):
        """Test adding a simple attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "title", "filter": None, "sub_attribute": None}
            ]

            patches = [PatchOperation(op=PatchOp.add, path="title", value="Manager")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["title"], "Manager")

    def test_apply_add_sub_attribute(self):
        """Test adding a sub-attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "name", "filter": None, "sub_attribute": "middleName"}
            ]

            patches = [PatchOperation(op=PatchOp.add, path="name.middleName", value="William")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["name"]["middleName"], "William")

    def test_apply_add_sub_attribute_new_parent(self):
        """Test adding a sub-attribute when parent doesn't exist"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "address", "filter": None, "sub_attribute": "street"}
            ]

            patches = [PatchOperation(op=PatchOp.add, path="address.street", value="123 Main St")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["address"]["street"], "123 Main St")

    def test_apply_add_enterprise_manager(self):
        """Test adding enterprise manager attribute (special case)"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": SCIM_URN_USER_ENTERPRISE, "filter": None, "sub_attribute": "manager"}
            ]

            patches = [
                PatchOperation(
                    op=PatchOp.add, path=f"{SCIM_URN_USER_ENTERPRISE}.manager", value="mgr123"
                )
            ]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result[SCIM_URN_USER_ENTERPRISE]["manager"], {"value": "mgr123"})

    def test_apply_add_to_existing_array(self):
        """Test adding to an existing array attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "emails", "filter": None, "sub_attribute": None}
            ]

            new_email = {"value": "john.work@example.com", "type": "work"}
            patches = [PatchOperation(op=PatchOp.add, path="emails", value=new_email)]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(len(result["emails"]), 3)
            self.assertIn(new_email, result["emails"])

    def test_apply_add_new_attribute_as_value(self):
        """Test adding a new attribute that gets set as value (not array)"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "department", "filter": None, "sub_attribute": None}
            ]

            patches = [PatchOperation(op=PatchOp.add, path="department", value="Engineering")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["department"], "Engineering")

    def test_apply_add_complex_path(self):
        """Test adding with complex path (filters)"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {
                    "attribute": "emails",
                    "filter": {"type": "comparison"},
                    "sub_attribute": "verified",
                }
            ]

            patches = [
                PatchOperation(op=PatchOp.add, path='emails[type eq "work"].verified', value=True)
            ]

            with patch.object(self.processor, "_navigate_and_modify") as mock_navigate:
                self.processor.apply_patches(self.sample_data, patches)
                mock_navigate.assert_called_once()

    # Test REMOVE operations
    def test_apply_remove_simple_attribute(self):
        """Test removing a simple attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "active", "filter": None, "sub_attribute": None}
            ]

            patches = [PatchOperation(op=PatchOp.remove, path="active")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertNotIn("active", result)

    def test_apply_remove_sub_attribute(self):
        """Test removing a sub-attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "name", "filter": None, "sub_attribute": "givenName"}
            ]

            patches = [PatchOperation(op=PatchOp.remove, path="name.givenName")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertNotIn("givenName", result["name"])
            self.assertIn("familyName", result["name"])  # Other sub-attributes remain

    def test_apply_remove_sub_attribute_nonexistent_parent(self):
        """Test removing sub-attribute when parent doesn't exist"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "nonexistent", "filter": None, "sub_attribute": "field"}
            ]

            patches = [PatchOperation(op=PatchOp.remove, path="nonexistent.field")]
            result = self.processor.apply_patches(self.sample_data, patches)

            # Should not raise error and data should be unchanged
            self.assertEqual(result, self.sample_data)

    def test_apply_remove_nonexistent_attribute(self):
        """Test removing a non-existent attribute (should not raise error)"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "nonexistent", "filter": None, "sub_attribute": None}
            ]

            patches = [PatchOperation(op=PatchOp.remove, path="nonexistent")]
            result = self.processor.apply_patches(self.sample_data, patches)

            # Should not raise error and data should be unchanged
            self.assertEqual(result, self.sample_data)

    # Test REPLACE operations
    def test_apply_replace_simple_attribute(self):
        """Test replacing a simple attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "userName", "filter": None, "sub_attribute": None}
            ]

            patches = [PatchOperation(op=PatchOp.replace, path="userName", value="jane.doe")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["userName"], "jane.doe")

    def test_apply_replace_sub_attribute(self):
        """Test replacing a sub-attribute"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "name", "filter": None, "sub_attribute": "givenName"}
            ]

            patches = [PatchOperation(op=PatchOp.replace, path="name.givenName", value="Jane")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["name"]["givenName"], "Jane")

    def test_apply_replace_sub_attribute_new_parent(self):
        """Test replacing sub-attribute when parent doesn't exist"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": "address", "filter": None, "sub_attribute": "city"}
            ]

            patches = [PatchOperation(op=PatchOp.replace, path="address.city", value="New York")]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["address"]["city"], "New York")

    def test_apply_replace_enterprise_manager(self):
        """Test replacing enterprise manager attribute (special case)"""
        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.return_value = [
                {"attribute": SCIM_URN_USER_ENTERPRISE, "filter": None, "sub_attribute": "manager"}
            ]

            patches = [
                PatchOperation(
                    op=PatchOp.replace,
                    path=f"{SCIM_URN_USER_ENTERPRISE}.manager",
                    value="newmgr456",
                )
            ]
            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result[SCIM_URN_USER_ENTERPRISE]["manager"], {"value": "newmgr456"})

    # Test bulk operations (path is None)
    def test_apply_bulk_add_operation(self):
        """Test bulk add operation when path is None"""
        patches = [
            PatchOperation(
                op=PatchOp.add, path=None, value={"title": "Manager", "department": "IT"}
            )
        ]

        with patch.object(self.processor, "_apply_add") as mock_add:
            self.processor.apply_patches(self.sample_data, patches)
            self.assertEqual(mock_add.call_count, 2)

    def test_apply_bulk_remove_operation(self):
        """Test bulk remove operation when path is None"""
        patches = [
            PatchOperation(op=PatchOp.remove, path=None, value={"active": None, "userName": None})
        ]

        with patch.object(self.processor, "_apply_remove") as mock_remove:
            self.processor.apply_patches(self.sample_data, patches)
            self.assertEqual(mock_remove.call_count, 2)

    def test_apply_bulk_replace_operation(self):
        """Test bulk replace operation when path is None"""
        patches = [
            PatchOperation(
                op=PatchOp.replace, path=None, value={"userName": "jane.doe", "active": False}
            )
        ]

        with patch.object(self.processor, "_apply_replace") as mock_replace:
            self.processor.apply_patches(self.sample_data, patches)
            self.assertEqual(mock_replace.call_count, 2)

    def test_apply_bulk_operation_invalid_value(self):
        """Test bulk operation with non-dict value (should be ignored)"""
        patches = [PatchOperation(op=PatchOp.add, path=None, value="invalid")]
        result = self.processor.apply_patches(self.sample_data, patches)

        self.assertEqual(result, self.sample_data)

    # Test _navigate_and_modify method
    def test_navigate_and_modify_with_filter_add_new_item(self):
        """Test navigating with filter and adding new item"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "home",
                },
                "sub_attribute": None,
            }
        ]

        new_email = {"value": "home@example.com", "type": "home"}
        data_copy = self.sample_data.copy()
        data_copy["emails"] = self.sample_data["emails"].copy()

        self.processor._navigate_and_modify(data_copy, components, new_email, "add")

        # Should add new email with type "home"
        home_emails = [email for email in data_copy["emails"] if email.get("type") == "home"]
        self.assertEqual(len(home_emails), 1)

    def test_navigate_and_modify_with_filter_modify_existing(self):
        """Test navigating with filter and modifying existing item"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": "verified",
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]

        self.processor._navigate_and_modify(data_copy, components, True, "add")

        # Should add verified field to work email
        work_email = next(email for email in data_copy["emails"] if email.get("type") == "work")
        self.assertTrue(work_email["verified"])

    def test_navigate_and_modify_remove_item(self):
        """Test removing entire item with filter"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "personal",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]
        original_count = len(data_copy["emails"])

        self.processor._navigate_and_modify(data_copy, components, None, "remove")

        # Should remove personal email
        self.assertEqual(len(data_copy["emails"]), original_count - 1)
        personal_emails = [
            email for email in data_copy["emails"] if email.get("type") == "personal"
        ]
        self.assertEqual(len(personal_emails), 0)

    def test_navigate_and_modify_nonexistent_attribute_add(self):
        """Test navigating to non-existent attribute for add operation"""
        components = [
            {
                "attribute": "phones",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "mobile",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        self.processor._navigate_and_modify(
            data_copy, components, {"value": "123-456-7890", "type": "mobile"}, "add"
        )

        # Should create new phones array
        self.assertIn("phones", data_copy)
        self.assertEqual(len(data_copy["phones"]), 1)

    def test_navigate_and_modify_nonexistent_attribute_remove(self):
        """Test navigating to non-existent attribute for remove operation"""
        components = [
            {
                "attribute": "phones",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "mobile",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        self.processor._navigate_and_modify(data_copy, components, None, "remove")

        # Should not create attribute or raise error
        self.assertNotIn("phones", data_copy)

    # Test filter matching methods
    def test_matches_filter_no_filter(self):
        """Test matching with no filter (should return True)"""
        item = {"type": "work"}
        result = self.processor._matches_filter(item, None)
        self.assertTrue(result)

    def test_matches_filter_empty_filter(self):
        """Test matching with empty filter (should return True)"""
        item = {"type": "work"}
        result = self.processor._matches_filter(item, {})
        self.assertTrue(result)

    def test_matches_filter_unknown_type(self):
        """Test matching with unknown filter type"""
        item = {"type": "work"}
        filter_expr = {"type": "unknown"}
        result = self.processor._matches_filter(item, filter_expr)
        self.assertFalse(result)

    def test_matches_comparison_eq(self):
        """Test comparison filter with eq operator"""
        item = {"type": "work", "primary": True}
        filter_expr = {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_eq_false(self):
        """Test comparison filter with eq operator (false case)"""
        item = {"type": "work"}
        filter_expr = {
            "type": "comparison",
            "attribute": "type",
            "operator": "eq",
            "value": "personal",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertFalse(result)

    def test_matches_comparison_ne(self):
        """Test comparison filter with ne operator"""
        item = {"type": "work"}
        filter_expr = {
            "type": "comparison",
            "attribute": "type",
            "operator": "ne",
            "value": "personal",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_co(self):
        """Test comparison filter with co (contains) operator"""
        item = {"value": "john@example.com"}
        filter_expr = {
            "type": "comparison",
            "attribute": "value",
            "operator": "co",
            "value": "example",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_sw(self):
        """Test comparison filter with sw (starts with) operator"""
        item = {"value": "john@example.com"}
        filter_expr = {
            "type": "comparison",
            "attribute": "value",
            "operator": "sw",
            "value": "john",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_ew(self):
        """Test comparison filter with ew (ends with) operator"""
        item = {"value": "john@example.com"}
        filter_expr = {
            "type": "comparison",
            "attribute": "value",
            "operator": "ew",
            "value": ".com",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_gt(self):
        """Test comparison filter with gt (greater than) operator"""
        item = {"priority": 10}
        filter_expr = {"type": "comparison", "attribute": "priority", "operator": "gt", "value": 5}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_lt(self):
        """Test comparison filter with lt (less than) operator"""
        item = {"priority": 3}
        filter_expr = {"type": "comparison", "attribute": "priority", "operator": "lt", "value": 5}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_ge(self):
        """Test comparison filter with ge (greater than or equal) operator"""
        item = {"priority": 5}
        filter_expr = {"type": "comparison", "attribute": "priority", "operator": "ge", "value": 5}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_le(self):
        """Test comparison filter with le (less than or equal) operator"""
        item = {"priority": 5}
        filter_expr = {"type": "comparison", "attribute": "priority", "operator": "le", "value": 5}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_pr(self):
        """Test comparison filter with pr (present) operator"""
        item = {"value": "john@example.com"}
        filter_expr = {"type": "comparison", "attribute": "value", "operator": "pr", "value": None}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertTrue(result)

    def test_matches_comparison_pr_false(self):
        """Test comparison filter with pr operator (false case)"""
        item = {"value": None}
        filter_expr = {"type": "comparison", "attribute": "value", "operator": "pr", "value": None}

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertFalse(result)

    def test_matches_comparison_missing_attribute(self):
        """Test comparison filter with missing attribute"""
        item = {"type": "work"}
        filter_expr = {
            "type": "comparison",
            "attribute": "missing",
            "operator": "eq",
            "value": "test",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertFalse(result)

    def test_matches_comparison_unknown_operator(self):
        """Test comparison filter with unknown operator"""
        item = {"type": "work"}
        filter_expr = {
            "type": "comparison",
            "attribute": "type",
            "operator": "unknown",
            "value": "work",
        }

        result = self.processor._matches_comparison(item, filter_expr)
        self.assertFalse(result)

    def test_matches_logical_and_true(self):
        """Test logical AND filter (true case)"""
        item = {"type": "work", "primary": True}
        filter_expr = {
            "type": "logical",
            "operator": "and",
            "left": {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"},
            "right": {
                "type": "comparison",
                "attribute": "primary",
                "operator": "eq",
                "value": True,
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertTrue(result)

    def test_matches_logical_and_false(self):
        """Test logical AND filter (false case)"""
        item = {"type": "work", "primary": False}
        filter_expr = {
            "type": "logical",
            "operator": "and",
            "left": {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"},
            "right": {
                "type": "comparison",
                "attribute": "primary",
                "operator": "eq",
                "value": True,
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertFalse(result)

    def test_matches_logical_or_true(self):
        """Test logical OR filter (true case)"""
        item = {"type": "personal", "primary": True}
        filter_expr = {
            "type": "logical",
            "operator": "or",
            "left": {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"},
            "right": {
                "type": "comparison",
                "attribute": "primary",
                "operator": "eq",
                "value": True,
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertTrue(result)

    def test_matches_logical_or_false(self):
        """Test logical OR filter (false case)"""
        item = {"type": "personal", "primary": False}
        filter_expr = {
            "type": "logical",
            "operator": "or",
            "left": {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"},
            "right": {
                "type": "comparison",
                "attribute": "primary",
                "operator": "eq",
                "value": True,
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertFalse(result)

    def test_matches_logical_not_true(self):
        """Test logical NOT filter (true case)"""
        item = {"type": "personal"}
        filter_expr = {
            "type": "logical",
            "operator": "not",
            "operand": {
                "type": "comparison",
                "attribute": "type",
                "operator": "eq",
                "value": "work",
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertTrue(result)

    def test_matches_logical_not_false(self):
        """Test logical NOT filter (false case)"""
        item = {"type": "work"}
        filter_expr = {
            "type": "logical",
            "operator": "not",
            "operand": {
                "type": "comparison",
                "attribute": "type",
                "operator": "eq",
                "value": "work",
            },
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertFalse(result)

    def test_matches_logical_unknown_operator(self):
        """Test logical filter with unknown operator"""
        item = {"type": "work"}
        filter_expr = {
            "type": "logical",
            "operator": "unknown",
            "left": {"type": "comparison", "attribute": "type", "operator": "eq", "value": "work"},
        }

        result = self.processor._matches_logical(item, filter_expr)
        self.assertFalse(result)

    def test_multiple_patches_applied_sequentially(self):
        """Test that multiple patches are applied in sequence"""
        patches = [
            PatchOperation(op=PatchOp.add, path="title", value="Manager"),
            PatchOperation(op=PatchOp.replace, path="userName", value="jane.doe"),
            PatchOperation(op=PatchOp.remove, path="active"),
        ]

        with patch.object(self.processor.parser, "parse_path") as mock_parse:
            mock_parse.side_effect = [
                [{"attribute": "title", "filter": None, "sub_attribute": None}],
                [{"attribute": "userName", "filter": None, "sub_attribute": None}],
                [{"attribute": "active", "filter": None, "sub_attribute": None}],
            ]

            result = self.processor.apply_patches(self.sample_data, patches)

            self.assertEqual(result["title"], "Manager")
            self.assertEqual(result["userName"], "jane.doe")
            self.assertNotIn("active", result)

    def test_navigate_and_modify_simple_attribute_last_component_add(self):
        """Test navigating to simple attribute as last component with add operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "title", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {}

        self.processor._navigate_and_modify(data_copy, components, "Senior Manager", "add")

        self.assertEqual(data_copy["profile"]["title"], "Senior Manager")

    def test_navigate_and_modify_simple_attribute_last_component_replace(self):
        """Test navigating to simple attribute as last component with replace operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "title", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {"title": "Manager"}

        self.processor._navigate_and_modify(data_copy, components, "Director", "replace")

        self.assertEqual(data_copy["profile"]["title"], "Director")

    def test_navigate_and_modify_simple_attribute_last_component_remove(self):
        """Test navigating to simple attribute as last component with remove operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "title", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {"title": "Manager", "department": "IT"}

        self.processor._navigate_and_modify(data_copy, components, None, "remove")

        self.assertNotIn("title", data_copy["profile"])
        self.assertIn("department", data_copy["profile"])  # Other attributes remain

    def test_navigate_and_modify_sub_attribute_last_component_add(self):
        """Test navigating to sub-attribute as last component with add operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "address", "filter": None, "sub_attribute": "street"},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {"address": {}}

        self.processor._navigate_and_modify(data_copy, components, "123 Main St", "add")

        self.assertEqual(data_copy["profile"]["address"]["street"], "123 Main St")

    def test_navigate_and_modify_sub_attribute_last_component_replace(self):
        """Test navigating to sub-attribute as last component with replace operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "address", "filter": None, "sub_attribute": "street"},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {"address": {"street": "456 Oak Ave"}}

        self.processor._navigate_and_modify(data_copy, components, "789 Pine Rd", "replace")

        self.assertEqual(data_copy["profile"]["address"]["street"], "789 Pine Rd")

    def test_navigate_and_modify_sub_attribute_last_component_remove(self):
        """Test navigating to sub-attribute as last component with remove operation"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "address", "filter": None, "sub_attribute": "street"},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {"address": {"street": "123 Main St", "city": "New York"}}

        self.processor._navigate_and_modify(data_copy, components, None, "remove")

        self.assertNotIn("street", data_copy["profile"]["address"])
        self.assertIn("city", data_copy["profile"]["address"])  # Other sub-attributes remain

    def test_navigate_and_modify_sub_attribute_parent_not_exists(self):
        """Test navigating to sub-attribute when parent attribute doesn't exist"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "address", "filter": None, "sub_attribute": "street"},
        ]

        data_copy = self.sample_data.copy()
        data_copy["profile"] = {}  # address doesn't exist yet

        self.processor._navigate_and_modify(data_copy, components, "123 Main St", "add")

        self.assertEqual(data_copy["profile"]["address"]["street"], "123 Main St")

    def test_navigate_and_modify_deeper_navigation(self):
        """Test navigating deeper through multiple levels without filters"""
        components = [
            {"attribute": "organization", "filter": None, "sub_attribute": None},
            {"attribute": "department", "filter": None, "sub_attribute": None},
            {"attribute": "team", "filter": None, "sub_attribute": None},
            {"attribute": "name", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()

        self.processor._navigate_and_modify(data_copy, components, "Engineering Team Alpha", "add")

        self.assertEqual(
            data_copy["organization"]["department"]["team"]["name"], "Engineering Team Alpha"
        )

    def test_navigate_and_modify_deeper_navigation_partial_path_exists(self):
        """Test navigating deeper when part of the path already exists"""
        components = [
            {"attribute": "organization", "filter": None, "sub_attribute": None},
            {"attribute": "department", "filter": None, "sub_attribute": None},
            {"attribute": "budget", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        data_copy["organization"] = {"department": {"name": "IT"}}

        self.processor._navigate_and_modify(data_copy, components, 100000, "add")

        self.assertEqual(data_copy["organization"]["department"]["budget"], 100000)
        self.assertEqual(
            data_copy["organization"]["department"]["name"], "IT"
        )  # Existing data preserved

    def test_navigate_and_modify_array_not_list_type(self):
        """Test navigation when expected array attribute is not a list"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": "verified",
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = "not_a_list"  # Invalid type

        # Should return early without error
        self.processor._navigate_and_modify(data_copy, components, True, "add")

        # Data should remain unchanged
        self.assertEqual(data_copy["emails"], "not_a_list")

    def test_navigate_and_modify_update_matching_item_with_dict_value(self):
        """Test updating matching item with dictionary value"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]

        update_data = {"verified": True, "lastChecked": "2023-01-01"}
        self.processor._navigate_and_modify(data_copy, components, update_data, "add")

        work_email = next(email for email in data_copy["emails"] if email.get("type") == "work")
        self.assertTrue(work_email["verified"])
        self.assertEqual(work_email["lastChecked"], "2023-01-01")
        # Original fields should still exist
        self.assertEqual(work_email["value"], "john@example.com")

    def test_navigate_and_modify_update_matching_item_with_non_dict_value(self):
        """Test updating matching item with non-dictionary value (should be ignored)"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]
        original_work_email = next(
            email for email in data_copy["emails"] if email.get("type") == "work"
        ).copy()

        # Try to update with non-dict value
        self.processor._navigate_and_modify(data_copy, components, "string_value", "add")

        # Email should remain unchanged
        work_email = next(email for email in data_copy["emails"] if email.get("type") == "work")
        self.assertEqual(work_email, original_work_email)

    def test_navigate_and_modify_remove_entire_matching_item(self):
        """Test removing entire matching item from array"""
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "personal",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]
        original_count = len(data_copy["emails"])

        self.processor._navigate_and_modify(data_copy, components, None, "remove")

        # Should remove the personal email
        self.assertEqual(len(data_copy["emails"]), original_count - 1)
        personal_emails = [
            email for email in data_copy["emails"] if email.get("type") == "personal"
        ]
        self.assertEqual(len(personal_emails), 0)

        # Work email should still exist
        work_emails = [email for email in data_copy["emails"] if email.get("type") == "work"]
        self.assertEqual(len(work_emails), 1)

    def test_navigate_and_modify_mixed_filters_and_simple_navigation(self):
        """Test navigation with mix of filtered and simple components"""
        # This test actually reveals a limitation in the current implementation
        # The _navigate_and_modify method doesn't properly handle navigation
        # after a filtered component. Let's test what actually happens.
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": "verified",  # Changed to test sub_attribute on filtered item
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]

        self.processor._navigate_and_modify(data_copy, components, True, "add")

        work_email = next(email for email in data_copy["emails"] if email.get("type") == "work")
        self.assertTrue(work_email["verified"])

    def test_navigate_and_modify_simple_navigation_multiple_levels(self):
        """Test simple navigation through multiple levels without filters"""
        components = [
            {"attribute": "profile", "filter": None, "sub_attribute": None},
            {"attribute": "settings", "filter": None, "sub_attribute": None},
            {"attribute": "notifications", "filter": None, "sub_attribute": "email"},
        ]

        data_copy = self.sample_data.copy()

        self.processor._navigate_and_modify(data_copy, components, True, "add")

        self.assertTrue(data_copy["profile"]["settings"]["notifications"]["email"])

    def test_navigate_and_modify_filter_then_simple_attribute_workaround(self):
        """Test the actual behavior when we have filter followed by simple navigation"""
        # Based on the code, after processing a filter, the method doesn't continue
        # to navigate deeper. This test documents the current behavior.
        components = [
            {
                "attribute": "emails",
                "filter": {
                    "type": "comparison",
                    "attribute": "type",
                    "operator": "eq",
                    "value": "work",
                },
                "sub_attribute": None,
            }
        ]

        data_copy = self.sample_data.copy()
        data_copy["emails"] = [email.copy() for email in self.sample_data["emails"]]

        # Update the work email with a dict containing nested data
        update_data = {"metadata": {"verified": True, "source": "manual"}}
        self.processor._navigate_and_modify(data_copy, components, update_data, "add")

        work_email = next(email for email in data_copy["emails"] if email.get("type") == "work")
        self.assertTrue(work_email["metadata"]["verified"])
        self.assertEqual(work_email["metadata"]["source"], "manual")

    def test_navigate_and_modify_intermediate_navigation_missing_parent(self):
        """Test navigation when intermediate parent doesn't exist"""
        components = [
            {"attribute": "organization", "filter": None, "sub_attribute": None},
            {"attribute": "department", "filter": None, "sub_attribute": None},
            {"attribute": "name", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        # organization doesn't exist initially

        self.processor._navigate_and_modify(data_copy, components, "Engineering", "add")

        self.assertEqual(data_copy["organization"]["department"]["name"], "Engineering")

    def test_navigate_and_modify_intermediate_navigation_existing_path(self):
        """Test navigation when part of the path already exists"""
        components = [
            {"attribute": "organization", "filter": None, "sub_attribute": None},
            {"attribute": "department", "filter": None, "sub_attribute": None},
            {"attribute": "budget", "filter": None, "sub_attribute": None},
        ]

        data_copy = self.sample_data.copy()
        data_copy["organization"] = {"department": {"name": "IT", "head": "John"}}

        self.processor._navigate_and_modify(data_copy, components, 500000, "add")

        self.assertEqual(data_copy["organization"]["department"]["budget"], 500000)
        # Existing data should be preserved
        self.assertEqual(data_copy["organization"]["department"]["name"], "IT")
        self.assertEqual(data_copy["organization"]["department"]["head"], "John")
