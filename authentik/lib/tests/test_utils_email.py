"""Test email utils"""

from django.test import TestCase

from authentik.lib.utils.email import normalize_addresses


class TestNormalizeAddresses(TestCase):
    """Test normalize_addresses"""

    def test_none(self):
        """None returns None"""
        self.assertIsNone(normalize_addresses(None))

    def test_plain_string(self):
        """Plain email string"""
        self.assertEqual(normalize_addresses("user@example.com"), [("", "user@example.com")])

    def test_formatted_string(self):
        """RFC 5322 formatted string keeps the name"""
        self.assertEqual(
            normalize_addresses("John Doe <user@example.com>"),
            [("John Doe", "user@example.com")],
        )
        self.assertEqual(
            normalize_addresses('"Doe, John" <user@example.com>'),
            [("Doe, John", "user@example.com")],
        )

    def test_tuple(self):
        """(name, email) tuple"""
        self.assertEqual(
            normalize_addresses(("John Doe", "user@example.com")),
            [("John Doe", "user@example.com")],
        )
        self.assertEqual(
            normalize_addresses((None, "user@example.com")),
            [("", "user@example.com")],
        )

    def test_mixed_list(self):
        """List of mixed formats"""
        self.assertEqual(
            normalize_addresses(
                [
                    "plain@example.com",
                    "Jane <jane@example.com>",
                    ("John", "john@example.com"),
                    ["Listed", "listed@example.com"],
                ]
            ),
            [
                ("", "plain@example.com"),
                ("Jane", "jane@example.com"),
                ("John", "john@example.com"),
                ("Listed", "listed@example.com"),
            ],
        )

    def test_invalid(self):
        """Invalid inputs raise ValueError"""
        with self.assertRaises(ValueError):
            normalize_addresses([])
        with self.assertRaises(ValueError):
            normalize_addresses(123)
        with self.assertRaises(ValueError):
            normalize_addresses(("only-one",))
        with self.assertRaises(ValueError):
            normalize_addresses([123])
