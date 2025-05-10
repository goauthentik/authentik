"""Test SMS API"""

from unittest.mock import MagicMock, patch
from urllib.parse import parse_qsl

from django.urls import reverse
from requests_mock import Mocker

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.crypto.generators import generate_id
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.authenticator_sms.models import (
    AuthenticatorSMSStage,
    SMSDevice,
    SMSProviders,
    hash_phone_number,
)
from authentik.stages.authenticator_sms.stage import PLAN_CONTEXT_PHONE, SESSION_KEY_SMS_DEVICE
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


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

    def test_stage_submit_twilio(self):
        """test stage (submit) (twilio)"""
        self.stage.account_sid = generate_id()
        self.stage.auth = generate_id()
        self.stage.from_number = generate_id()
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
        number = generate_id()

        with Mocker() as mocker:
            mocker.post(
                (
                    "https://api.twilio.com/2010-04-01/Accounts/"
                    f"{self.stage.account_sid}/Messages.json"
                ),
                json={},
            )
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
                data={"component": "ak-stage-authenticator-sms", "phone_number": number},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(mocker.call_count, 1)
            self.assertEqual(mocker.request_history[0].method, "POST")
            request_body = dict(parse_qsl(mocker.request_history[0].body))
            device: SMSDevice = self.client.session[SESSION_KEY_SMS_DEVICE]
            self.assertEqual(
                request_body,
                {
                    "To": number,
                    "From": self.stage.from_number,
                    "Body": f"Use this code to authenticate in authentik: {device.token}",
                },
            )
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            response_errors={},
            phone_number_required=False,
        )

    def test_stage_context_data(self):
        """test stage context data"""
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        sms_send_mock = MagicMock()
        with (
            patch(
                (
                    "authentik.stages.authenticator_sms.stage."
                    "AuthenticatorSMSStageView._has_phone_number"
                ),
                MagicMock(
                    return_value="1234",
                ),
            ),
            patch(
                "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send",
                sms_send_mock,
            ),
        ):
            response = self.client.get(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug}),
            )
            sms_send_mock.assert_called_once()
        self.assertStageResponse(
            response,
            self.flow,
            self.user,
            component="ak-stage-authenticator-sms",
            phone_number_required=False,
        )

    def test_stage_context_data_duplicate(self):
        """test stage context data (phone number exists already)"""
        self.client.get(
            reverse("authentik_flows:configure", kwargs={"stage_uuid": self.stage.stage_uuid}),
        )
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        plan.context[PLAN_CONTEXT_PROMPT] = {
            PLAN_CONTEXT_PHONE: "1234",
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        SMSDevice.objects.create(
            phone_number="1234",
            user=self.user,
            stage=self.stage,
        )
        sms_send_mock = MagicMock()
        with (
            patch(
                "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send",
                sms_send_mock,
            ),
        ):
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
        plan: FlowPlan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.context[PLAN_CONTEXT_PROMPT], {})

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
