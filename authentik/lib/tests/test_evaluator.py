"""Test Evaluator base functions"""
from django.test import TestCase

from authentik.core.tests.utils import create_test_admin_user
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
        user = create_test_admin_user()
        self.assertIsNotNone(BaseEvaluator.expr_user_by(username=user.username))
        self.assertIsNone(BaseEvaluator.expr_user_by(username="bar"))
        self.assertIsNone(BaseEvaluator.expr_user_by(foo="bar"))

    def test_is_group_member(self):
        """Test expr_is_group_member"""
        self.assertFalse(BaseEvaluator.expr_is_group_member(create_test_admin_user(), name="test"))
