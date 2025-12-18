"""test uuid utils"""

from django.test import TestCase

from authentik.lib.utils.uuid import is_uuid_valid


class TestUUID(TestCase):
    """test uuid utils"""

    def test_uuid_valid(self):
        self.assertTrue(is_uuid_valid("00000000-0000-0000-0000-000000000000"))
        self.assertTrue(is_uuid_valid("9f2fd607-36a8-420f-9260-44f8416e7f6d"))

    def test_uuid_invalid(self):
        self.assertFalse(is_uuid_valid(""))
        self.assertFalse(is_uuid_valid("123"))
