"""evaluator tests"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.policies.expression.evaluator import Evaluator
from passbook.policies.types import PolicyRequest


class TestEvaluator(TestCase):
    """Evaluator tests"""

    def setUp(self):
        self.request = PolicyRequest(user=get_anonymous_user())

    def test_valid(self):
        """test simple value expression"""
        template = "return True"
        evaluator = Evaluator()
        evaluator.set_policy_request(self.request)
        self.assertEqual(evaluator.evaluate(template).passing, True)

    def test_messages(self):
        """test expression with message return"""
        template = 'pb_message("some message");return False'
        evaluator = Evaluator()
        evaluator.set_policy_request(self.request)
        result = evaluator.evaluate(template)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("some message",))

    def test_invalid_syntax(self):
        """test invalid syntax"""
        template = ";"
        evaluator = Evaluator()
        evaluator.set_policy_request(self.request)
        result = evaluator.evaluate(template)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("invalid syntax (<string>, line 2)",))

    def test_undefined(self):
        """test undefined result"""
        template = "{{ foo.bar }}"
        evaluator = Evaluator()
        evaluator.set_policy_request(self.request)
        result = evaluator.evaluate(template)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("name 'foo' is not defined",))

    def test_validate(self):
        """test validate"""
        template = "True"
        evaluator = Evaluator()
        result = evaluator.validate(template)
        self.assertEqual(result, True)

    def test_validate_invalid(self):
        """test validate"""
        template = ";"
        evaluator = Evaluator()
        with self.assertRaises(ValidationError):
            evaluator.validate(template)
