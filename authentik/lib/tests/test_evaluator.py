"""Test Evaluator base functions"""

from unittest.mock import NonCallableMock, patch

from django.test import RequestFactory, TestCase
from django.urls import reverse
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_admin_user, create_test_flow, create_test_user
from authentik.events.models import Event
from authentik.lib.expression.evaluator import BaseEvaluator
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


class TestEvaluator(TestCase):
    """Test Evaluator base functions"""

    def test_expr_regex_match(self) -> None:
        """Test expr_regex_match"""
        self.assertFalse(BaseEvaluator.expr_regex_match("foo", "bar"))
        self.assertTrue(BaseEvaluator.expr_regex_match("foo", "foo"))

    def test_expr_regex_replace(self) -> None:
        """Test expr_regex_replace"""
        self.assertEqual(BaseEvaluator.expr_regex_replace("foo", "o", "a"), "faa")

    def test_expr_user_by(self) -> None:
        """Test expr_user_by"""
        user = create_test_admin_user()
        self.assertIsNotNone(BaseEvaluator.expr_user_by(username=user.username))
        self.assertIsNone(BaseEvaluator.expr_user_by(username="bar"))
        self.assertIsNone(BaseEvaluator.expr_user_by(foo="bar"))

    def test_expr_is_group_member(self) -> None:
        """Test expr_is_group_member"""
        self.assertFalse(BaseEvaluator.expr_is_group_member(create_test_admin_user(), name="test"))

    def test_expr_event_create(self) -> None:
        """Test expr_event_create"""
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {
            "foo": "bar",
        }
        evaluator.evaluate("ak_create_event('foo', bar='baz')")
        event = Event.objects.filter(action="custom_foo").first()
        self.assertIsNotNone(event)
        assert event is not None  # nosec
        self.assertEqual(event.context, {"bar": "baz", "foo": "bar"})

    @apply_blueprint("system/providers-oauth2.yaml")
    def test_expr_create_jwt(self) -> None:
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

    @patch("authentik.stages.email.tasks.send_mails")
    def test_expr_send_email_with_body(self, mock_send_mails: NonCallableMock) -> None:
        """Test ak_send_email with body parameter"""
        user = create_test_user()
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {"user": user}

        # Test sending email with body
        result = evaluator.evaluate(
            "return ak_send_email('test@example.com', 'Test Subject', body='Test Body')"
        )

        self.assertTrue(result)
        mock_send_mails.assert_called_once()

        # Verify the call arguments - send_mails is called with (stage, message)
        args, kwargs = mock_send_mails.call_args
        stage, message = args

        # Check that global settings are used (stage is None)
        self.assertIsNone(stage)

        # Check message properties
        self.assertEqual(message.subject, "Test Subject")
        self.assertEqual(message.to, ["test@example.com"])
        self.assertEqual(message.body, "Test Body")

    @patch("authentik.stages.email.tasks.send_mails")
    def test_expr_send_email_with_template(self, mock_send_mails: NonCallableMock) -> None:
        """Test ak_send_email with template parameter"""
        user = create_test_user()
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {"user": user}

        # Test sending email with template
        result = evaluator.evaluate(
            "return ak_send_email('test@example.com', 'Test Subject', "
            "template='email/password_reset.html')"
        )

        self.assertTrue(result)
        mock_send_mails.assert_called_once()

    def test_expr_send_email_validation_errors(self) -> None:
        """Test ak_send_email validation errors"""
        evaluator = BaseEvaluator(generate_id())

        # Test error when both body and template are provided
        with self.assertRaises(ValueError) as cm:
            evaluator.evaluate(
                "return ak_send_email('test@example.com', 'Test', "
                "body='Body', template='template.html')"
            )
        self.assertIn("mutually exclusive", str(cm.exception))

        # Test error when neither body nor template are provided
        with self.assertRaises(ValueError) as cm:
            evaluator.evaluate("return ak_send_email('test@example.com', 'Test')")
        self.assertIn("Either body or template parameter must be provided", str(cm.exception))

    @patch("authentik.stages.email.tasks.send_mails")
    def test_expr_send_email_with_custom_stage(self, mock_send_mails: NonCallableMock) -> None:
        """Test ak_send_email with custom EmailStage"""
        from authentik.stages.email.models import EmailStage

        user = create_test_user()
        custom_stage = EmailStage(
            name="custom-stage", use_global_settings=False, from_address="custom@example.com"
        )

        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {"user": user, "custom_stage": custom_stage}

        # Test sending email with custom stage
        result = evaluator.evaluate(
            "return ak_send_email('test@example.com', 'Test Subject', "
            "body='Test Body', stage=custom_stage)"
        )

        self.assertTrue(result)
        mock_send_mails.assert_called_once()

        # Verify the custom stage was used
        args, kwargs = mock_send_mails.call_args
        stage, message = args

        self.assertEqual(stage, custom_stage)
        self.assertFalse(stage.use_global_settings)

    @patch("authentik.stages.email.tasks.send_mails")
    def test_expr_send_email_with_context(self, mock_send_mails: NonCallableMock) -> None:
        """Test ak_send_email with custom context parameter"""
        user = create_test_user()
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {"user": user, "request_id": "123"}

        # Test sending email with template and custom context
        result = evaluator.evaluate(
            "return ak_send_email('test@example.com', 'Test Subject', "
            "template='email/password_reset.html', "
            "context={'url': 'http://localhost', 'expires': '2026-01-01'})"
        )

        self.assertTrue(result)
        mock_send_mails.assert_called_once()

        # Verify the call arguments - send_mails is called with (stage, message)
        args, kwargs = mock_send_mails.call_args
        stage, message = args

        # Check that global settings are used (stage is None)
        self.assertIsNone(stage)

        self.assertEqual(message.subject, "Test Subject")
        self.assertEqual(message.to, ["test@example.com"])
        self.assertIn("2026-01-01", message.body)
        self.assertIn("http://localhost", message.body)

    @patch("authentik.stages.email.tasks.send_mails")
    def test_expr_send_email_multiple_addresses(self, mock_send_mails: NonCallableMock) -> None:
        """Test ak_send_email with multiple email addresses"""
        user = create_test_user()
        evaluator = BaseEvaluator(generate_id())
        evaluator._context = {"user": user}

        # Test sending email to multiple addresses
        result = evaluator.evaluate(
            "return ak_send_email(['user1@example.com', 'user2@example.com'], "
            "'Test Subject', body='Test Body')"
        )

        self.assertTrue(result)
        mock_send_mails.assert_called_once()

        # Verify the call arguments - send_mails is called with (stage, message)
        args, kwargs = mock_send_mails.call_args
        stage, message = args

        # Check that global settings are used (stage is None)
        self.assertIsNone(stage)

        # Check message properties - should have multiple recipients
        self.assertEqual(message.subject, "Test Subject")
        self.assertEqual(message.to, ["user1@example.com", "user2@example.com"])
        self.assertEqual(message.body, "Test Body")

    def test_expr_send_email_multiple_addresses_validation(self) -> None:
        """Test ak_send_email validation with multiple addresses"""
        evaluator = BaseEvaluator(generate_id())

        # Test error when empty list is provided
        with self.assertRaises(ValueError) as cm:
            evaluator.evaluate("return ak_send_email([], 'Test', body='Body')")
        self.assertIn("Address list cannot be empty", str(cm.exception))

        # Test error when invalid type is provided
        with self.assertRaises(ValueError) as cm:
            evaluator.evaluate("return ak_send_email(123, 'Test', body='Body')")
        self.assertIn("Address must be a string or list of strings", str(cm.exception))
