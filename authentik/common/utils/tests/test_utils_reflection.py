"""Test Reflection utils"""

from datetime import datetime

from django.test import TestCase

from authentik.common.utils.reflection import path_to_class


class TestReflectionUtils(TestCase):
    """Test Reflection-utils"""

    def test_path_to_class(self):
        """Test path_to_class"""
        self.assertEqual(path_to_class("datetime.datetime"), datetime)
