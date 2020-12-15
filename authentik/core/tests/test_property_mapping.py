"""authentik core property mapping tests"""
from django.test import TestCase

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import PropertyMapping
from authentik.events.models import Event, EventAction


class TestPropertyMappings(TestCase):
    """authentik core property mapping tests"""

    def test_expression(self):
        """Test expression"""
        mapping = PropertyMapping.objects.create(
            name="test", expression="return 'test'"
        )
        self.assertEqual(mapping.evaluate(None, None), "test")

    def test_expression_syntax(self):
        """Test expression syntax error"""
        mapping = PropertyMapping.objects.create(name="test", expression="-")
        with self.assertRaises(PropertyMappingExpressionException):
            mapping.evaluate(None, None)

    def test_expression_error_general(self):
        """Test expression error"""
        expr = "return aaa"
        mapping = PropertyMapping.objects.create(name="test", expression=expr)
        with self.assertRaises(NameError):
            mapping.evaluate(None, None)
        self.assertTrue(
            Event.objects.filter(
                action=EventAction.PROPERTY_MAPPING_EXCEPTION, context__expression=expr
            ).exists()
        )
