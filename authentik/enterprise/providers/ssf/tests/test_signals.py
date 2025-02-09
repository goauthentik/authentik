from uuid import uuid4

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import Application
from authentik.core.tests.utils import (
    create_test_cert,
    create_test_user,
)
from authentik.enterprise.providers.ssf.models import (
    SSFEventStatus,
    SSFProvider,
    Stream,
    StreamEvent,
)
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class TestSignals(APITestCase):
    """Test individual SSF Signals"""

    def setUp(self):
        self.application = Application.objects.create(name=generate_id(), slug=generate_id())
        self.provider = SSFProvider.objects.create(
            name=generate_id(),
            signing_key=create_test_cert(),
            backchannel_application=self.application,
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
            HTTP_AUTHORIZATION=f"Bearer {self.provider.token.key}",
        )
        self.assertEqual(res.status_code, 201, res.content)

    def test_signal_logout(self):
        """Test user logout"""
        user = create_test_user()
        self.client.force_login(user)
        self.client.logout()

        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        event_payload = event.payload["events"][
            "https://schemas.openid.net/secevent/caep/event-type/session-revoked"
        ]
        self.assertEqual(event_payload["initiating_entity"], "user")
        self.assertEqual(event_payload["subject"]["session"]["format"], "opaque")
        self.assertEqual(event_payload["subject"]["user"]["format"], "email")
        self.assertEqual(event_payload["subject"]["user"]["email"], user.email)

    def test_signal_password_change(self):
        """Test user password change"""
        user = create_test_user()
        self.client.force_login(user)
        user.set_password(generate_id())
        user.save()

        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        event_payload = event.payload["events"][
            "https://schemas.openid.net/secevent/caep/event-type/credential-change"
        ]
        self.assertEqual(event_payload["change_type"], "update")
        self.assertEqual(event_payload["credential_type"], "password")
        self.assertEqual(event_payload["subject"]["user"]["format"], "email")
        self.assertEqual(event_payload["subject"]["user"]["email"], user.email)

    def test_signal_authenticator_added(self):
        """Test authenticator creation signal"""
        user = create_test_user()
        self.client.force_login(user)
        dev = WebAuthnDevice.objects.create(
            user=user,
            name=generate_id(),
            credential_id=generate_id(),
            public_key=generate_id(),
            aaguid=str(uuid4()),
        )

        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).exclude().first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        event_payload = event.payload["events"][
            "https://schemas.openid.net/secevent/caep/event-type/credential-change"
        ]
        self.assertEqual(event_payload["change_type"], "create")
        self.assertEqual(event_payload["fido2_aaguid"], dev.aaguid)
        self.assertEqual(event_payload["friendly_name"], dev.name)
        self.assertEqual(event_payload["credential_type"], "fido-u2f")
        self.assertEqual(event_payload["subject"]["user"]["format"], "email")
        self.assertEqual(event_payload["subject"]["user"]["email"], user.email)

    def test_signal_authenticator_deleted(self):
        """Test authenticator deletion signal"""
        user = create_test_user()
        self.client.force_login(user)
        dev = WebAuthnDevice.objects.create(
            user=user,
            name=generate_id(),
            credential_id=generate_id(),
            public_key=generate_id(),
            aaguid=str(uuid4()),
        )
        dev.delete()

        stream = Stream.objects.filter(provider=self.provider).first()
        self.assertIsNotNone(stream)
        event = StreamEvent.objects.filter(stream=stream).exclude().first()
        self.assertIsNotNone(event)
        self.assertEqual(event.status, SSFEventStatus.PENDING_FAILED)
        event_payload = event.payload["events"][
            "https://schemas.openid.net/secevent/caep/event-type/credential-change"
        ]
        self.assertEqual(event_payload["change_type"], "delete")
        self.assertEqual(event_payload["fido2_aaguid"], dev.aaguid)
        self.assertEqual(event_payload["friendly_name"], dev.name)
        self.assertEqual(event_payload["credential_type"], "fido-u2f")
        self.assertEqual(event_payload["subject"]["user"]["format"], "email")
        self.assertEqual(event_payload["subject"]["user"]["email"], user.email)
