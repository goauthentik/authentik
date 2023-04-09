"""authentik core property mapping tests"""
from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.exceptions import PropertyMappingExpressionException
from authentik.core.models import PropertyMapping
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy


class TestPropertyMappings(TestCase):
    """authentik core property mapping tests"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.factory = RequestFactory()

    def test_expression(self):
        """Test expression"""
        mapping = PropertyMapping.objects.create(name=generate_id(), expression="return 'test'")
        self.assertEqual(mapping.evaluate(None, None), "test")

    def test_expression_syntax(self):
        """Test expression syntax error"""
        mapping = PropertyMapping.objects.create(name=generate_id(), expression="-")
        with self.assertRaises(PropertyMappingExpressionException):
            mapping.evaluate(None, None)

    def test_expression_error_general(self):
        """Test expression error"""
        expr = "return aaa"
        mapping = PropertyMapping.objects.create(name=generate_id(), expression=expr)
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
        mapping = PropertyMapping.objects.create(name=generate_id(), expression=expr)
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

    def test_call_policy(self):
        """test ak_call_policy"""
        expr = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression="return request.http_request.path",
        )
        http_request = self.factory.get("/")
        tmpl = (
            """
        res = ak_call_policy('%s')
        result = [request.http_request.path, res.raw_result]
        return result
        """
            % expr.name
        )
        evaluator = PropertyMapping(expression=tmpl, name=generate_id())
        res = evaluator.evaluate(self.user, http_request)
        self.assertEqual(res, ["/", "/"])
