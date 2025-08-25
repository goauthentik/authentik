"""Telegram source tests"""

import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.sources.telegram.stage import TelegramChallengeResponse
from authentik.stages.identification.models import IdentificationStage, UserFields


class MockTelegramResponseMixin:
    def _add_hash(self, response):
        to_hash = "\n".join([f"{key}={value}" for key, value in sorted(response.items())])
        response["hash"] = hmac.new(
            hashlib.sha256(self.source.bot_token.encode("utf-8")).digest(),
            to_hash.encode("utf-8"),
            "sha256",
        ).hexdigest()

    def _make_valid_response(self):
        resp = {
            "id": "123456789",
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "auth_date": str(int(datetime.now().timestamp())),
        }
        self._add_hash(resp)
        return resp

    def _make_outdated_response(self):
        resp = self._make_valid_response()
        resp["auth_date"] = str(int((datetime.now() - timedelta(days=1)).timestamp()))
        self._add_hash(resp)
        return resp


class TestTelegramSource(MockTelegramResponseMixin, TestCase):
    """Telegram Source tests"""

    def setUp(self):
        from authentik.sources.telegram.models import TelegramSource

        self.source = TelegramSource.objects.create(
            name="test",
            slug="test",
            bot_username="test_bot",
            bot_token="modern_token",  # nosec
            request_message_access=True,
        )
        self.mock_stage = Mock()
        self.mock_stage.source = self.source

    def test_ui_login_button(self):
        """Test UI login button"""
        ui_login_button = self.source.ui_login_button(None)
        self.assertIsNotNone(ui_login_button)
        self.assertEqual(ui_login_button.name, "test")
        self.assertTrue(ui_login_button.challenge.is_valid(raise_exception=True))

    def test_challenge_response(self):
        """Test correct Telegram response validation"""
        cr = TelegramChallengeResponse(data=self._make_valid_response())
        cr.stage = self.mock_stage
        self.assertTrue(cr.is_valid(raise_exception=True))

    def test_outdated_challenge_response(self):
        """Test outdated Telegram response validation"""
        cr = TelegramChallengeResponse(data=self._make_outdated_response())
        cr.stage = self.mock_stage
        with self.assertRaises(ValidationError):
            cr.is_valid(raise_exception=True)

    def test_invalid_hash_challenge_response(self):
        """Test invalid hash in Telegram response validation"""
        resp = self._make_valid_response()
        resp["hash"] = "invalid_hash"
        cr = TelegramChallengeResponse(data=resp)
        cr.stage = self.mock_stage
        with self.assertRaises(ValidationError):
            cr.is_valid(raise_exception=True)

    def test_user_base_properties(self):
        """Test user base properties"""
        cr = TelegramChallengeResponse(data=self._make_valid_response())
        cr.stage = self.mock_stage
        cr.is_valid(raise_exception=True)
        properties = self.source.get_base_user_properties(info=cr.validated_data)
        self.assertEqual(
            properties,
            {
                "username": "testuser",
                "name": "Test User",
                "email": None,
            },
        )

    def test_group_base_properties(self):
        """Test group base properties"""
        for group_id in ["group 1", "group 2"]:
            properties = self.source.get_base_group_properties(group_id=group_id)
            self.assertEqual(properties, {"name": group_id})


class TestTelegramViews(MockTelegramResponseMixin, FlowTestCase):
    """Test Telegram source views"""

    def setUp(self):
        super().setUp()
        from authentik.sources.telegram.models import TelegramSource

        self.source = TelegramSource.objects.create(
            name="test",
            slug="test",
            bot_username="test_bot",
            bot_token="modern_token",  # nosec
            request_message_access=True,
            enrollment_flow=create_test_flow(),
        )

        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = IdentificationStage.objects.create(
            name="identification",
            user_fields=[UserFields.E_MAIL],
            pretend_user_exists=False,
        )
        self.stage.sources.set([self.source])
        self.stage.save()
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def _make_initial_request(self):
        return self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

    def _make_start_request(self):
        return self.client.get(
            reverse("authentik_sources_telegram:start", kwargs={"source_slug": self.source.slug}),
            follow=True,
        )

    def test_start_view(self):
        """Test TelegramStartView"""
        self.assertEqual(self._make_initial_request().status_code, 200)

        response = self._make_start_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.redirect_chain[0][0],
            reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug}),
        )

    def test_challenge_view(self):
        """Test TelegramLoginView"""
        self._make_initial_request()
        self._make_start_request()

        form_data = self._make_valid_response()
        form_data["component"] = "ak-source-telegram"
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, form_data)
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(
            response,
            reverse(
                "authentik_core:if-flow", kwargs={"flow_slug": self.source.enrollment_flow.slug}
            ),
        )
