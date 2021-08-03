"""authentik core property mapping tests"""
from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import PropertyMapping
from authentik.events.models import Event, EventAction


class TestPropertyMappings(TestCase):
    """authentik core property mapping tests"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_expression(self):
        """Test expression"""
        mapping = PropertyMapping.objects.create(name="test", expression="return 'test'")
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
        with self.assertRaises(PropertyMappingExpressionException):
            mapping.evaluate(None, None)
        events = Event.objects.filter(
            action=EventAction.PROPERTY_MAPPING_EXCEPTION, context__expression=expr
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)

    def test_expression_error_extended(self):
        """Test expression error (with user and http request"""
        expr = "return aaa"
        request = self.factory.get("/")
        mapping = PropertyMapping.objects.create(name="test", expression=expr)
        with self.assertRaises(PropertyMappingExpressionException):
            mapping.evaluate(get_anonymous_user(), request)
        events = Event.objects.filter(
            action=EventAction.PROPERTY_MAPPING_EXCEPTION, context__expression=expr
        )
        self.assertTrue(events.exists())
        self.assertEqual(len(events), 1)
        event = events.first()
        self.assertEqual(event.user["username"], "AnonymousUser")
        self.assertEqual(event.client_ip, "127.0.0.1")
