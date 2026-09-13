import json
from dataclasses import asdict
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow, create_test_user
from authentik.enterprise.providers.ssf.models import (
    SSFEventStatus,
    SSFProvider,
    Stream,
    StreamEvent,
    StreamStatus,
)
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import AccessToken, OAuth2Provider


class TestStream(APITestCase):
    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
        )

    def test_stream_add_token(self):
        """test stream add (token auth)"""
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "iss": "https://authentik.company/.well-known/ssf-configuration/foo/5",
                "aud": ["https://app.authentik.company"],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/push",
                    "endpoint_url": "https://app.authentik.company",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/credential-change",
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 201)
        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        self.assertEqual(
            event.payload["events"],
            {"https://schemas.openid.net/secevent/ssf/event-type/verification": {}},
        )

    def test_stream_add_poll(self):
        """test stream add - poll method"""
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "iss": "https://authentik.company/.well-known/ssf-configuration/foo/5",
                "aud": ["https://app.authentik.company"],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/poll",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/credential-change",
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content,
            {"delivery": {"method": ["Polling for SSF events is not currently supported."]}},
        )

    def test_stream_delete(self):
        """delete stream"""
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.delete(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 204)
        stream.refresh_from_db()
        self.assertEqual(stream.status, StreamStatus.DISABLED_DELETED)

    def test_stream_get(self):
        """get stream"""
        Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)

    def test_stream_get_filter_query(self):
        """get stream"""
        other_stream = Stream.objects.create(provider=self.provider)
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            )
            + f"?stream_id={stream.pk}",
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(str(stream.pk), res.content.decode())
        self.assertNotIn(str(other_stream.pk), res.content.decode())

    def test_stream_patch(self):
        """patch stream"""
        other_stream = Stream.objects.create(provider=self.provider)
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.patch(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "delivery": {"endpoint_url": "https://localhost"},
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(str(stream.pk), res.content.decode())
        self.assertNotIn(str(other_stream.pk), res.content.decode())

    def test_stream_put(self):
        """put stream"""
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.put(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "iss": "https://authentik.company/.well-known/ssf-configuration/foo/5",
                "aud": ["https://app.authentik.company"],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/push",
                    "endpoint_url": "https://app.authentik.company",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/credential-change",
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn(str(stream.pk), res.content.decode())
        stream.refresh_from_db()
        self.assertEqual(stream.aud, ["https://app.authentik.company"])

    def test_stream_verify(self):
        """Test stream verify"""
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream-verify",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 204)

    def test_stream_status(self):
        """Test stream status"""
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream-status",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(
            res.content,
            {
                "stream_id": str(stream.pk),
                "status": str(stream.status),
            },
        )

    def test_stream_status_not_found(self):
        """Test stream status"""
        Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream-status",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(uuid4()),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 404)

    def test_stream_status_update(self):
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream-status",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
                "status": StreamStatus.DISABLED,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 200)
        stream.refresh_from_db()
        self.assertJSONEqual(
            res.content,
            {
                "stream_id": str(stream.pk),
                "status": str(stream.status),
            },
        )


class TestStreamAuthorization(APITestCase):
    """Stream management endpoints require the add_stream permission on the provider.
    A user authenticated with an ordinary access token issued by the backchannel
    application's provider does not hold that permission and must be rejected."""

    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
        )
        self.oauth_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        self.application.provider = self.oauth_provider
        self.application.save()
        self.user = create_test_user()
        self.token = AccessToken.objects.create(
            provider=self.oauth_provider,
            user=self.user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(asdict(IDToken("foo", "bar"))),
        )

    def test_stream_get(self):
        """get stream without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertNotIn(str(stream.pk), res.content.decode())

    def test_stream_patch(self):
        """patch stream without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider, aud=["https://one.example.com"])
        res = self.client.patch(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "aud": ["https://two.example.com"],
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        stream.refresh_from_db()
        self.assertEqual(stream.aud, ["https://one.example.com"])

    def test_stream_put(self):
        """put stream without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider, aud=["https://one.example.com"])
        res = self.client.put(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "aud": ["https://two.example.com"],
                "delivery": {
                    "method": "https://schemas.openid.net/secevent/risc/delivery-method/push",
                    "endpoint_url": "https://two.example.com",
                },
                "events_requested": [
                    "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
                ],
                "format": "iss_sub",
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        stream.refresh_from_db()
        self.assertEqual(stream.aud, ["https://one.example.com"])

    def test_stream_delete(self):
        """delete stream without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.delete(
            reverse(
                "authentik_providers_ssf:stream",
                kwargs={"application_slug": self.application.slug},
            ),
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        stream.refresh_from_db()
        self.assertEqual(stream.status, StreamStatus.ENABLED)

    def test_stream_verify(self):
        """verify stream without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream-verify",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        self.assertFalse(StreamEvent.objects.filter(stream=stream).exists())

    def test_stream_status(self):
        """get stream status without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.get(
            reverse(
                "authentik_providers_ssf:stream-status",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)

    def test_stream_status_update(self):
        """update stream status without add_stream permission"""
        self.assertFalse(self.user.has_perm("authentik_providers_ssf.add_stream", self.provider))
        stream = Stream.objects.create(provider=self.provider)
        res = self.client.post(
            reverse(
                "authentik_providers_ssf:stream-status",
                kwargs={"application_slug": self.application.slug},
            ),
            data={
                "stream_id": str(stream.pk),
                "status": StreamStatus.DISABLED,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.token.token}",
        )
        self.assertEqual(res.status_code, 403)
        stream.refresh_from_db()
        self.assertEqual(stream.status, StreamStatus.ENABLED)
