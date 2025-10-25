import json
from dataclasses import asdict

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.enterprise.providers.ssf.models import (
    SSFEventStatus,
    SSFProvider,
    Stream,
    StreamEvent,
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
            {"https://schemas.openid.net/secevent/ssf/event-type/verification": {"state": None}},
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

    def test_stream_add_oidc(self):
        """test stream add (oidc auth)"""
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
        )
        self.application.provider = provider
        self.application.save()
        user = create_test_admin_user()
        token = AccessToken.objects.create(
            provider=provider,
            user=user,
            token=generate_id(),
            auth_time=timezone.now(),
            _scope="openid user profile",
            _id_token=json.dumps(
                asdict(
                    IDToken("foo", "bar"),
                )
            ),
        )

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
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertEqual(res.status_code, 201)
        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        self.assertEqual(
            event.payload["events"],
            {"https://schemas.openid.net/secevent/ssf/event-type/verification": {"state": None}},
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
        self.assertFalse(Stream.objects.filter(pk=stream.pk).exists())
