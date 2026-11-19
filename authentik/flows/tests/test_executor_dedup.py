"""flow executor duplicate-submission deduplication tests"""

from threading import Event as ThreadEvent
from threading import Thread
from time import monotonic
from unittest.mock import patch

from django.db import connection
from django.test import Client, TransactionTestCase
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.events.models import Event, EventAction
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.lib.generators import generate_id
from authentik.stages.authenticator.oath import TOTP
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.identification.models import IdentificationStage, UserFields
from authentik.stages.user_login.models import UserLoginStage


class TestFlowExecutorDuplicateSubmission(TransactionTestCase):
    """Test a client that sends every flow submission twice, concurrently"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.device = TOTPDevice.objects.create(user=self.user, confirmed=True)
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        stages = [
            IdentificationStage.objects.create(
                name=generate_id(), user_fields=[UserFields.USERNAME]
            ),
            AuthenticatorValidateStage.objects.create(
                name=generate_id(), device_classes=[DeviceClasses.TOTP]
            ),
            UserLoginStage.objects.create(name=generate_id()),
        ]
        for order, stage in enumerate(stages):
            FlowStageBinding.objects.create(target=self.flow, stage=stage, order=order)
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def _waiting_locks(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_locks WHERE NOT granted")
            return cursor.fetchone()[0]

    def test_duplicate_totp_submission_logs_in_once(self):
        """A user whose TOTP code is submitted twice at once is logged in without a
        failed login, whichever response reaches the browser"""
        self.client.get(self.url)
        self.client.post(
            self.url, {"uid_field": self.user.username}, content_type="application/json"
        )
        self.client.get(self.url)
        duplicate_client = Client()
        duplicate_client.cookies = self.client.cookies
        body = {
            "component": "ak-stage-authenticator-validate",
            "code": TOTP(self.device.bin_key).token(),
        }

        entered = ThreadEvent()
        release = ThreadEvent()
        responses = {}
        errors = []
        verify_token = TOTPDevice.verify_token

        # Holds the first submission mid-verification so the duplicate overlaps it
        def held_verify_token(device, token):
            entered.set()
            if not release.wait(timeout=10):
                errors.append("first submission was never released")
            return verify_token(device, token)

        def submit(name: str, client: Client):
            try:
                responses[name] = client.post(self.url, body, content_type="application/json")
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
            finally:
                connection.close()

        with patch.object(TOTPDevice, "verify_token", autospec=True, side_effect=held_verify_token):
            first = Thread(target=submit, args=("first", self.client))
            first.start()
            self.assertTrue(entered.wait(timeout=10), "first submission never reached TOTP")
            duplicate = Thread(target=submit, args=("duplicate", duplicate_client))
            duplicate.start()
            deadline = monotonic() + 10
            # Wait until the duplicate is queued behind the first or has finished
            while duplicate.is_alive() and self._waiting_locks() < 1:
                self.assertLess(monotonic(), deadline, "duplicate never reached the server")
            release.set()
            first.join(timeout=15)
            duplicate.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertEqual(responses["first"].status_code, 302)
        self.assertEqual(responses["duplicate"].status_code, 302)
        self.assertFalse(Event.objects.filter(action=EventAction.LOGIN_FAILED).exists())
        # The browser follows whichever redirect it received; the flow finishes either way
        response = duplicate_client.get(self.url)
        self.assertEqual(response.json()["component"], "xak-flow-redirect")
        self.assertEqual(Event.objects.filter(action=EventAction.LOGIN).count(), 1)
