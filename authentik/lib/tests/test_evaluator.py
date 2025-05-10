"""Test Evaluator base functions"""

from django.test import RequestFactory, TestCase
from django.urls import reverse
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.expression.evaluator import BaseEvaluator
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.crypto.generators import generate_id
from authentik.events.models import Event
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


class TestEvaluator(TestCase):
    """Test Evaluator base functions"""

    def test_expr_regex_match(self):
        """Test expr_regex_match"""
        self.assertFalse(BaseEvaluator.expr_regex_match("foo", "bar"))
        self.assertTrue(BaseEvaluator.expr_regex_match("foo", "foo"))

    def test_expr_regex_replace(self):
        """Test expr_regex_replace"""
        self.assertEqual(BaseEvaluator.expr_regex_replace("foo", "o", "a"), "faa")

    def test_expr_user_by(self):
        """Test expr_user_by"""
        user = create_test_admin_user()
        self.assertIsNotNone(BaseEvaluator.expr_user_by(username=user.username))
        self.assertIsNone(BaseEvaluator.expr_user_by(username="bar"))
        self.assertIsNone(BaseEvaluator.expr_user_by(foo="bar"))

    def test_expr_is_group_member(self):
        """Test expr_is_group_member"""
        self.assertFalse(BaseEvaluator.expr_is_group_member(create_test_admin_user(), name="test"))

    def test_expr_event_create(self):
        """Test expr_event_create"""
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {
            "foo": "bar",
        }
        evaluator.evaluate("ak_create_event('foo', bar='baz')")
        event = Event.objects.filter(action="custom_foo").first()
        self.assertIsNotNone(event)
        self.assertEqual(event.context, {"bar": "baz", "foo": "bar"})

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_expr_create_jwt(self):
        """Test expr_create_jwt"""
        rf = RequestFactory()
        user = create_test_user()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-email",
                    "goauthentik.io/providers/oauth2/scope-profile",
                ]
            )
        )
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {
            "http_request": rf.get(reverse("authentik_core:root-redirect")),
            "user": user,
            "provider": provider.name,
        }
        jwt = evaluator.evaluate(
            "return ak_create_jwt(user, provider, ['openid', 'email', 'profile'])"
        )
        decoded = decode(
            jwt, provider.client_secret, algorithms=["HS256"], audience=provider.client_id
        )
        self.assertEqual(decoded["preferred_username"], user.username)
