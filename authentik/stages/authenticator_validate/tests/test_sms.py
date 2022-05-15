"""Test validator stage"""
from time import sleep

from django.test.client import RequestFactory
from django.urls.base import reverse

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_sms.models import AuthenticatorSMSStage, SMSDevice, SMSProviders
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
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
        conf_stage = IdentificationStage.objects.create(
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
        # Verify token once here to set last_t etc
        token = device.generate_token()
        device.verify_token(token)
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="milliseconds=0",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.SMS],
        )
        sleep(1)
        stage.configuration_stages.set([conf_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertStageResponse(
            response,
            flow,
            component="ak-stage-authenticator-validate",
        )

    def test_last_auth_threshold_valid(self):
        """Test last_auth_threshold"""
        conf_stage = IdentificationStage.objects.create(
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
        # Verify token once here to set last_t etc
        token = device.generate_token()
        device.verify_token(token)
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.SMS],
        )
        stage.configuration_stages.set([conf_stage])
        flow = Flow.objects.create(name="test", slug="test", title="test")
        FlowStageBinding.objects.create(target=flow, stage=conf_stage, order=0)
        FlowStageBinding.objects.create(target=flow, stage=stage, order=1)

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            {"uid_field": self.user.username},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
            follow=True,
        )
        self.assertStageResponse(response, component="xak-flow-redirect", to="/")
