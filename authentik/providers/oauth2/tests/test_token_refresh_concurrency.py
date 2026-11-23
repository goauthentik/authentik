"""Test concurrent refresh token rotation"""

from base64 import b64encode
from datetime import datetime, timedelta
from http import HTTPStatus
from json import dumps, loads
from threading import Barrier, Thread
from unittest.mock import patch

from django.db import connection
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils.timezone import now

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import GRANT_TYPE_REFRESH_TOKEN
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    AccessToken,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
)

CONCURRENT_REQUESTS = 8


class TestRefreshTokenConcurrency(TransactionTestCase):
    """Several requests presenting the same refresh token at the same time, each on its own
    database connection. They all load the token while it is still active, and only then try to
    consume it, which is when a read-then-write would issue a successor to each of them."""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.app = Application.objects.create(name=generate_id(), slug=generate_id())

    def _create_provider(self, **kwargs) -> tuple[OAuth2Provider, str]:
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            client_type=ClientType.CONFIDENTIAL,
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=create_test_cert(),
            grant_types=[GrantType.REFRESH_TOKEN],
            **kwargs,
        )
        provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        self.app.provider = provider
        self.app.save()
        header = b64encode(f"{provider.client_id}:{provider.client_secret}".encode()).decode()
        return provider, header

    def _create_refresh_token(self, provider: OAuth2Provider) -> RefreshToken:
        return RefreshToken.objects.create(
            provider=provider,
            user=self.user,
            _id_token=dumps({}),
            auth_time=now(),
            _scope="offline_access",
            expires=now() + timedelta(days=30),
        )

    def _refresh_concurrently(self, header: str, raw: str) -> list[tuple[int, dict]]:
        """Send `CONCURRENT_REQUESTS` refresh requests for `raw` at once. Every request waits
        right before consuming the token until all of them have loaded it"""
        barrier = Barrier(CONCURRENT_REQUESTS, timeout=30)
        consume = RefreshToken.consume

        def consume_together(token: RefreshToken, at: datetime) -> bool:
            barrier.wait()
            return consume(token, at)

        results: list[tuple[int, dict]] = []
        errors: list[BaseException] = []

        def refresh():
            try:
                response = Client().post(
                    reverse("authentik_providers_oauth2:token"),
                    data={
                        "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                        "refresh_token": raw,
                    },
                    HTTP_AUTHORIZATION=f"Basic {header}",
                )
                results.append((response.status_code, loads(response.content.decode())))
            except BaseException as exc:  # noqa: BLE001
                errors.append(exc)
                barrier.abort()
            finally:
                connection.close()

        with patch.object(RefreshToken, "consume", autospec=True, side_effect=consume_together):
            threads = [Thread(target=refresh) for _ in range(CONCURRENT_REQUESTS)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(results), CONCURRENT_REQUESTS)
        return results

    def _successors(self, token: RefreshToken):
        return RefreshToken.objects.filter(family=token.family).exclude(pk=token.pk)

    def _assert_one_winner(self, results: list[tuple[int, dict]]) -> str:
        succeeded = [body for status, body in results if status == HTTPStatus.OK]
        self.assertEqual(len(succeeded), 1, results)
        for status, body in results:
            if status != HTTPStatus.OK:
                self.assertEqual(status, HTTPStatus.BAD_REQUEST)
                self.assertEqual(body["error"], "invalid_grant")
        return succeeded[0]["refresh_token"]

    def test_concurrent_refresh_without_family_revocation(self):
        """Exactly one request gets a successor, the others are rejected as reuse"""
        provider, header = self._create_provider(refresh_token_revoke_family_on_reuse=False)
        token = self._create_refresh_token(provider)
        winner = self._assert_one_winner(self._refresh_concurrently(header, token.token))
        token.refresh_from_db()
        self.assertTrue(token.revoked)
        self.assertIsNotNone(token.rotated_at)
        successor = self._successors(token).get()
        self.assertFalse(successor.revoked)
        self.assertEqual(
            successor.pk, RefreshToken.objects.get(RefreshToken.token_query(winner)).pk
        )
        # Rejected requests don't get an access token either
        self.assertEqual(AccessToken.objects.count(), 1)
        self.assertEqual(
            Event.objects.filter(action=EventAction.SUSPICIOUS_REQUEST).count(),
            CONCURRENT_REQUESTS - 1,
        )

    def test_concurrent_refresh_without_grace_period(self):
        """Exactly one request gets a successor, and the others revoke its family"""
        provider, header = self._create_provider(
            refresh_token_reuse_grace_period="seconds=0"  # nosec
        )
        token = self._create_refresh_token(provider)
        self._assert_one_winner(self._refresh_concurrently(header, token.token))
        self.assertEqual(self._successors(token).count(), 1)
        self.assertFalse(RefreshToken.objects.filter(revoked=False).exists())
        self.assertFalse(AccessToken.objects.filter(revoked=False).exists())

    def test_concurrent_refresh_within_grace_period(self):
        """One request consumes the token, the others use the grace period: each gets its own
        token in the same family"""
        provider, header = self._create_provider()
        token = self._create_refresh_token(provider)
        results = self._refresh_concurrently(header, token.token)
        self.assertEqual([status for status, _ in results], [200] * CONCURRENT_REQUESTS, results)
        issued = {body["refresh_token"] for _, body in results}
        self.assertEqual(len(issued), CONCURRENT_REQUESTS)
        successors = self._successors(token)
        self.assertEqual(successors.count(), CONCURRENT_REQUESTS)
        self.assertFalse(successors.filter(revoked=True).exists())
        self.assertFalse(Event.objects.filter(action=EventAction.SUSPICIOUS_REQUEST).exists())
