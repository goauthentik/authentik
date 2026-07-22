"""Test SMS utils"""

from django.test import TestCase

from authentik.lib.utils.sms import mask_phone_number


class TestSMSUtils(TestCase):
    """Test SMS utils"""

    def test_mask_phone_number(self):
        """Test mask_phone_number"""
        self.assertEqual(mask_phone_number("+12025550173"), "+*******0173")
        self.assertEqual(mask_phone_number("2025550173"), "******0173")

    def test_mask_phone_number_short(self):
        """Test mask_phone_number with numbers shorter than the visible window"""
        self.assertEqual(mask_phone_number("123"), "***")
        self.assertEqual(mask_phone_number("+123"), "+***")

    def test_mask_phone_number_empty(self):
        """Test mask_phone_number with empty input"""
        self.assertIsNone(mask_phone_number(None))
        self.assertIsNone(mask_phone_number(""))
