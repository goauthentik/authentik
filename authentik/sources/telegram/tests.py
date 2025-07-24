"""Telegram source tests"""

import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import Mock

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.sources.telegram.stage import TelegramChallengeResponse


class TestTelegramSource(TestCase):
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
