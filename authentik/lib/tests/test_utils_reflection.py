"""Test Reflection utils"""

from datetime import datetime

from django.test import TestCase

from authentik.lib.utils.reflection import ConditionalInheritance, path_to_class


class TestReflectionUtils(TestCase):
    """Test Reflection-utils"""

    def test_path_to_class(self):
        """Test path_to_class"""
        self.assertEqual(path_to_class("datetime.datetime"), datetime)

    def test_multiple_unavailable_mixins(self):
        """Multiple missing enterprise mixins must not create duplicate bases."""

        class Combined(
            ConditionalInheritance("missing.FirstMixin"),
            ConditionalInheritance("missing.SecondMixin"),
            list,
        ):
            pass

        self.assertEqual(Combined([1]), [1])
