"""Test SMS API"""
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import FlowStageBinding
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice, SMSProviders
from authentik.stages.authenticator_sms.stage import SESSION_KEY_SMS_DEVICE


class AuthenticatorSMSStageTests(APITestCase):
    """Test SMS API"""

    def setUp(self) -> None:
        super().setUp()
        self.flow = create_test_flow()
        self.stage: AuthenticatorSMSStage = AuthenticatorSMSStage.objects.create(
            name="foo",
            provider=SMSProviders.TWILIO,
            configure_flow=self.flow,
        )
        FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=0)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_stage_no_prefill(self):
        """test stage"""
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertJSONEqual(
            response.content,
            {
                "component": "ak-stage-authenticator-sms",
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": self.flow.title,
                    "layout": "stacked",
                },
                "pending_user": self.user.username,
                "pending_user_avatar": "/static/dist/assets/images/user_default.png",
                "phone_number_required": True,
                "type": ChallengeTypes.NATIVE.value,
            },
        )

    def test_stage_submit(self):
        """test stage (submit)"""
        # Prepares session etc
        self.test_stage_no_prefill()
        sms_send_mock = MagicMock()
        with patch(
            "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send",
            sms_send_mock,
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={"component": "ak-stage-authenticator-sms", "phone_number": "foo"},
            )
            self.assertEqual(response.status_code, 200)
            sms_send_mock.assert_called_once()

    def test_stage_submit_full(self):
        """test stage (submit)"""
        # Prepares session etc
        self.test_stage_submit()
        sms_send_mock = MagicMock()
        with patch(
            "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send",
            sms_send_mock,
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={
                    "component": "ak-stage-authenticator-sms",
                    "phone_number": "foo",
                    "code": int(self.client.session[SESSION_KEY_SMS_DEVICE].token),
                },
            )
            self.assertEqual(response.status_code, 200)
            sms_send_mock.assert_not_called()

    def test_stage_hash(self):
        """test stage (submit)"""
        self.stage.verify_only = True
        self.stage.save()
        # Prepares session etc
        self.test_stage_submit()
        sms_send_mock = MagicMock()
        with patch(
            "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send",
            sms_send_mock,
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={
                    "component": "ak-stage-authenticator-sms",
                    "phone_number": "foo",
                    "code": int(self.client.session[SESSION_KEY_SMS_DEVICE].token),
                },
            )
            self.assertEqual(response.status_code, 200)
            sms_send_mock.assert_not_called()
        device: SMSDevice = SMSDevice.objects.filter(user=self.user).first()
        self.assertTrue(device.is_hashed)
