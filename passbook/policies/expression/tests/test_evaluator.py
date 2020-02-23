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
        template = "True"
        evaluator = Evaluator()
        self.assertEqual(evaluator.evaluate(template, self.request).passing, True)

    def test_messages(self):
        """test expression with message return"""
        template = "False, 'some message'"
        evaluator = Evaluator()
        result = evaluator.evaluate(template, self.request)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("some message",))

    def test_invalid_syntax(self):
        """test invalid syntax"""
        template = "{%"
        evaluator = Evaluator()
        result = evaluator.evaluate(template, self.request)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("tag name expected",))

    def test_undefined(self):
        """test undefined result"""
        template = "{{ foo.bar }}"
        evaluator = Evaluator()
        result = evaluator.evaluate(template, self.request)
        self.assertEqual(result.passing, False)
        self.assertEqual(result.messages, ("'foo' is undefined",))

    def test_validate(self):
        """test validate"""
        template = "True"
        evaluator = Evaluator()
        result = evaluator.validate(template)
        self.assertEqual(result, True)

    def test_validate_invalid(self):
        """test validate"""
        template = "{%"
        evaluator = Evaluator()
        with self.assertRaises(ValidationError):
            evaluator.validate(template)
