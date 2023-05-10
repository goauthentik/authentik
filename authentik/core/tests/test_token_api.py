"""Test token API"""
from json import loads

from django.urls.base import reverse
from guardian.shortcuts import get_anonymous_user
from rest_framework.test import APITestCase

from authentik.core.api.tokens import TokenSerializer
from authentik.core.models import USER_ATTRIBUTE_TOKEN_EXPIRING, Token, TokenIntents, User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id


class TestTokenAPI(APITestCase):
    """Test token API"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username="testuser")
        self.admin = create_test_admin_user()
        self.client.force_login(self.user)

    def test_token_create(self):
        """Test token creation endpoint"""
        response = self.client.post(
            reverse("authentik_api:token-list"), {"identifier": "test-token"}
        )
        self.assertEqual(response.status_code, 201)
        token = Token.objects.get(identifier="test-token")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.expiring, True)
        self.assertTrue(self.user.has_perm("authentik_core.view_token_key", token))

    def test_token_set_key(self):
        """Test token creation endpoint"""
        response = self.client.post(
            reverse("authentik_api:token-list"), {"identifier": "test-token"}
        )
        self.assertEqual(response.status_code, 201)
        token = Token.objects.get(identifier="test-token")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.expiring, True)
        self.assertTrue(self.user.has_perm("authentik_core.view_token_key", token))

        self.client.force_login(self.admin)
        new_key = generate_id()
        response = self.client.post(
            reverse("authentik_api:token-set-key", kwargs={"identifier": token.identifier}),
            {"key": new_key},
        )
        self.assertEqual(response.status_code, 204)
        token.refresh_from_db()
        self.assertEqual(token.key, new_key)

    def test_token_create_invalid(self):
        """Test token creation endpoint (invalid data)"""
        response = self.client.post(
            reverse("authentik_api:token-list"),
            {"identifier": "test-token", "intent": TokenIntents.INTENT_RECOVERY},
        )
        self.assertEqual(response.status_code, 400)

    def test_token_create_non_expiring(self):
        """Test token creation endpoint"""
        self.user.attributes[USER_ATTRIBUTE_TOKEN_EXPIRING] = False
        self.user.save()
        response = self.client.post(
            reverse("authentik_api:token-list"), {"identifier": "test-token"}
        )
        self.assertEqual(response.status_code, 201)
        token = Token.objects.get(identifier="test-token")
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.intent, TokenIntents.INTENT_API)
        self.assertEqual(token.expiring, False)

    def test_list(self):
        """Test Token List (Test normal authentication)"""
        Token.objects.all().delete()
        token_should: Token = Token.objects.create(
            identifier="test", expiring=False, user=self.user
        )
        Token.objects.create(identifier="test-2", expiring=False, user=get_anonymous_user())
        response = self.client.get(reverse("authentik_api:token-list"))
        body = loads(response.content)
        self.assertEqual(len(body["results"]), 1)
        self.assertEqual(body["results"][0]["identifier"], token_should.identifier)

    def test_list_admin(self):
        """Test Token List (Test with admin auth)"""
        Token.objects.all().delete()
        self.client.force_login(self.admin)
        token_should: Token = Token.objects.create(
            identifier="test", expiring=False, user=self.user
        )
        token_should_not: Token = Token.objects.create(
            identifier="test-2", expiring=False, user=get_anonymous_user()
        )
        response = self.client.get(reverse("authentik_api:token-list"))
        body = loads(response.content)
        self.assertEqual(len(body["results"]), 2)
        self.assertEqual(body["results"][0]["identifier"], token_should.identifier)
        self.assertEqual(body["results"][1]["identifier"], token_should_not.identifier)

    def test_serializer_no_request(self):
        """Test serializer without request"""
        self.assertTrue(
            TokenSerializer(
                data={
                    "identifier": generate_id(),
                    "intent": TokenIntents.INTENT_APP_PASSWORD,
                    "key": generate_id(),
                    "user": self.user.pk,
                }
            ).is_valid(raise_exception=True)
        )
