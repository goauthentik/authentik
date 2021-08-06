"""Test Evaluator base functions"""
from django.test import TestCase

from authentik.core.models import User
from authentik.lib.expression.evaluator import BaseEvaluator


class TestEvaluator(TestCase):
    """Test Evaluator base functions"""

    def test_regex_match(self):
        """Test expr_regex_match"""
        self.assertFalse(BaseEvaluator.expr_regex_match("foo", "bar"))
        self.assertTrue(BaseEvaluator.expr_regex_match("foo", "foo"))

    def test_regex_replace(self):
        """Test expr_regex_replace"""
        self.assertEqual(BaseEvaluator.expr_regex_replace("foo", "o", "a"), "faa")

    def test_user_by(self):
        """Test expr_user_by"""
        self.assertIsNotNone(BaseEvaluator.expr_user_by(username="akadmin"))
        self.assertIsNone(BaseEvaluator.expr_user_by(username="bar"))
        self.assertIsNone(BaseEvaluator.expr_user_by(foo="bar"))

    def test_is_group_member(self):
        """Test expr_is_group_member"""
        self.assertFalse(
            BaseEvaluator.expr_is_group_member(User.objects.get(username="akadmin"), name="test")
        )
