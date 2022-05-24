"""Test validator stage"""
from unittest.mock import MagicMock, patch

from django.test.client import RequestFactory
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice, SMSProviders
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_validate.stage import COOKIE_NAME_MFA
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageSMSTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()
        self.stage = AuthenticatorSMSStage.objects.create(
            name="sms",
            provider=SMSProviders.GENERIC,
            from_number="1234",
        )

    def test_last_auth_threshold(self):
        """Test last_auth_threshold"""
        ident_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: SMSDevice = SMSDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.stage,
        )

        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="milliseconds=0",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.SMS],
        )
        stage.configuration_stages.set([ident_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        device.generate_token()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"code": device.token},
        )
        self.assertNotIn(COOKIE_NAME_MFA, response.cookies)

    def test_last_auth_threshold_valid(self):
        """Test last_auth_threshold"""
        ident_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: SMSDevice = SMSDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.stage,
        )

        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.SMS],
        )
        stage.configuration_stages.set([ident_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        send_mock = MagicMock()
        with patch(
            "authentik.stages.authenticator_sms.models.AuthenticatorSMSStage.send", send_mock
        ):
            response = self.client.post(
                reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
                {
                    "component": "ak-stage-authenticator-validate",
                    "selected_challenge": {
                        "device_class": "sms",
                        "device_uid": str(device.pk),
                        "challenge": {},
                    },
                },
            )
        self.assertEqual(send_mock.call_count, 1)
        device.generate_token()
        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"code": device.token},
        )
        self.assertIn(COOKIE_NAME_MFA, response.cookies)
        self.assertStageResponse(response, component="xak-flow-redirect", to="/")

    def test_sms_hashed(self):
        """Test hashed SMS device"""
        ident_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        SMSDevice.objects.create(
            user=self.user,
            confirmed=True,
            stage=self.stage,
            phone_number="hash:foo",
        )

        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.DENY,
            device_classes=[DeviceClasses.SMS],
        )
        stage.configuration_stages.set([ident_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=ident_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertStageResponse(response, flow, self.user, component="ak-stage-access-denied")
