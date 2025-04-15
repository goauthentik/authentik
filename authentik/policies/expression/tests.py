"""evaluator tests"""

from django.test import RequestFactory, TestCase
from guardian.shortcuts import get_anonymous_user
from rest_framework.serializers import ValidationError
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.lib.generators import generate_id
from authentik.policies.exceptions import PolicyException
from authentik.policies.expression.api import ExpressionPolicySerializer
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest


class TestEvaluator(TestCase):
    """Evaluator tests"""

    def setUp(self):
        factory = RequestFactory()
        self.http_request = factory.get("/")
        self.obj = Application.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        self.request = PolicyRequest(user=get_anonymous_user())
        self.request.obj = self.obj
        self.request.http_request = self.http_request

    def test_full(self):
        """Test full with Policy instance"""
        policy = ExpressionPolicy(name="test", expression="return 'test'")
        policy.save()
        request = PolicyRequest(get_anonymous_user())
        result = policy.passes(request)
        self.assertTrue(result.passing)

    def test_valid(self):
        """test simple value expression"""
        template = "return True"
        evaluator = PolicyEvaluator("test")
        evaluator.set_policy_request(self.request)
        self.assertEqual(evaluator.evaluate(template).passing, True)

    def test_messages(self):
        """test expression with message return"""
        template = 'ak_message("some message");return False'
        evaluator = PolicyEvaluator("test")
        evaluator.set_policy_request(self.request)
        result = evaluator.evaluate(template)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("some message",))

    def test_invalid_syntax(self):
        """test invalid syntax"""
        template = ";"
        evaluator = PolicyEvaluator("test")
        evaluator.set_policy_request(self.request)
        with self.assertRaises(PolicyException):
            evaluator.evaluate(template)

    def test_validate(self):
        """test validate"""
        template = "True"
        evaluator = PolicyEvaluator("test")
        result = evaluator.validate(template)
        self.assertEqual(result, True)

    def test_validate_invalid(self):
        """test validate"""
        template = ";"
        evaluator = PolicyEvaluator("test")
        with self.assertRaises(ValidationError):
            evaluator.validate(template)

    def test_execution_logging(self):
        """test execution_logging"""
        expr = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression="ak_message(request.http_request.path)\nreturn True",
        )
        evaluator = PolicyEvaluator("test")
        evaluator.set_policy_request(self.request)
        proc = PolicyProcess(PolicyBinding(policy=expr), request=self.request, result_queue=None)
        res = proc.profiling_wrapper()
        self.assertEqual(res.messages, ("/",))

    def test_call_policy(self):
        """test ak_call_policy"""
        expr = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression="ak_message(request.http_request.path)\nreturn True",
        )
        expr2 = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression=f"""
            ak_message(request.http_request.path)
            res = ak_call_policy('{expr.name}')
            ak_message(request.http_request.path)
            for msg in res.messages:
                ak_message(msg)
            """,
        )
        proc = PolicyProcess(PolicyBinding(policy=expr2), request=self.request, result_queue=None)
        res = proc.profiling_wrapper()
        self.assertEqual(res.messages, ("/", "/", "/"))

    def test_call_policy_test_like(self):
        """test ak_call_policy without `obj` set, as if it was when testing policies"""
        expr = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression="ak_message(request.http_request.path)\nreturn True",
        )
        expr2 = ExpressionPolicy.objects.create(
            name=generate_id(),
            execution_logging=True,
            expression=f"""
            ak_message(request.http_request.path)
            res = ak_call_policy('{expr.name}')
            ak_message(request.http_request.path)
            for msg in res.messages:
                ak_message(msg)
            """,
        )
        self.request.obj = None
        proc = PolicyProcess(PolicyBinding(policy=expr2), request=self.request, result_queue=None)
        res = proc.profiling_wrapper()
        self.assertEqual(res.messages, ("/", "/", "/"))


class TestExpressionPolicyAPI(APITestCase):
    """Test expression policy's API"""

    def test_validate(self):
        """Test ExpressionPolicy's validation"""
        # Because the root property-mapping has no write operation, we just instantiate
        # a serializer and test inline
        expr = "return True"
        self.assertEqual(ExpressionPolicySerializer().validate_expression(expr), expr)
        with self.assertRaises(ValidationError):
            ExpressionPolicySerializer().validate_expression("/")
