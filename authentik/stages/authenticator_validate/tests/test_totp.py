"""Test validator stage"""
from time import sleep

from django.test.client import RequestFactory
from django.urls.base import reverse
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.exceptions import ValidationError

from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow, FlowStageBinding, NotConfiguredAction
from authentik.flows.tests import FlowTestCase
from authentik.stages.authenticator_validate.challenge import (
    get_challenge_for_device,
    validate_challenge_code,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.identification.models import IdentificationStage, UserFields


class AuthenticatorValidateStageTOTPTests(FlowTestCase):
    """Test validator stage"""

    def setUp(self) -> None:
        self.user = create_test_admin_user()
        self.request_factory = RequestFactory()

    def test_last_auth_threshold(self):
        """Test last_auth_threshold"""
        conf_stage = IdentificationStage.objects.create(
            name="conf",
            user_fields=[
                UserFields.USERNAME,
            ],
        )
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        # Verify token once here to set last_t etc
        totp = TOTP(device.bin_key)
        sleep(1)
        self.assertTrue(device.verify_token(totp.token()))
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="milliseconds=0",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
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
        device: TOTPDevice = TOTPDevice.objects.create(
            user=self.user,
            confirmed=True,
        )
        # Verify token once here to set last_t etc
        totp = TOTP(device.bin_key)
        sleep(1)
        self.assertTrue(device.verify_token(totp.token()))
        stage = AuthenticatorValidateStage.objects.create(
            name="foo",
            last_auth_threshold="hours=1",
            not_configured_action=NotConfiguredAction.CONFIGURE,
            device_classes=[DeviceClasses.TOTP],
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

    def test_device_challenge_totp(self):
        """Test device challenge"""
        request = self.request_factory.get("/")
        totp_device = TOTPDevice.objects.create(user=self.user, confirmed=True, digits=6)
        self.assertEqual(get_challenge_for_device(request, totp_device), {})
        with self.assertRaises(ValidationError):
            validate_challenge_code("1234", request, self.user)
