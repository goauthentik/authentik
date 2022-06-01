"""Test SMS API"""
from unittest.mock import MagicMock, patch

from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_sms.models import (
    AuthenticatorSMSStage,
    SMSDevice,
    SMSProviders,
    hash_phone_number,
)


class AuthenticatorSMSStageTests(FlowTestCase):
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
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=True,
        )

    def test_stage_submit(self):
        """test stage (submit)"""
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=True,
        )
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
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            response_errors={},
            phone_number_required=False,
        )

    def test_stage_submit_full(self):
        """test stage (submit)"""
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=True,
        )
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
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            response_errors={},
            phone_number_required=False,
        )
        with patch(
            "authentik.stages.authenticator_sms.models.SMSDevice.verify_token",
            MagicMock(return_value=True),
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={
                    "component": "ak-stage-authenticator-sms",
                    "phone_number": "foo",
                    "code": "123456",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))

    def test_stage_hash(self):
        """test stage (verify_only)"""
        self.stage.verify_only = True
        self.stage.save()
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=True,
        )
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
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            response_errors={},
            phone_number_required=False,
        )
        with patch(
            "authentik.stages.authenticator_sms.models.SMSDevice.verify_token",
            MagicMock(return_value=True),
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={
                    "component": "ak-stage-authenticator-sms",
                    "phone_number": "foo",
                    "code": "123456",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        device: SMSDevice = SMSDevice.objects.filter(user=self.user).first()
        self.assertTrue(device.is_hashed)

    def test_stage_hash_twice(self):
        """test stage (hash + duplicate)"""
        SMSDevice.objects.create(
            user=create_test_admin_user(),
            stage=self.stage,
            phone_number=hash_phone_number("foo"),
        )
        self.stage.verify_only = True
        self.stage.save()
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
        )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=True,
        )
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
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            response_errors={
                "non_field_errors": [{"code": "invalid", "string": "Invalid phone number"}]
            },
            phone_number_required=False,
        )
