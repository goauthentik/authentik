"""TOTP Setup stage"""
from base64 import b32encode
from binascii import unhexlify
from typing import Any, Dict

import lxml.etree as ET  # nosec
from django.http import HttpRequest, HttpResponse
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django_otp.plugins.otp_totp.models import TOTPDevice
from qrcode import QRCode
from qrcode.image.svg import SvgFillImage
from structlog import get_logger

from passbook.flows.models import NotConfiguredAction, Stage
from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.stages.otp_time.forms import SetupForm
from passbook.stages.otp_time.models import OTPTimeStage

LOGGER = get_logger()
SESSION_TOTP_DEVICE = "totp_device"


def otp_auth_url(device: TOTPDevice) -> str:
    """Create otpauth according to
    https://github.com/google/google-authenticator/wiki/Key-Uri-Format"""
    # Ensure that the secret parameter is the FIRST parameter of the URI, this
    # allows Microsoft Authenticator to work.
    issuer = "passbook"

    rawkey = unhexlify(device.key.encode("ascii"))
    secret = b32encode(rawkey).decode("utf-8")

    query = [
        ("secret", secret),
        ("digits", device.digits),
        ("issuer", issuer),
    ]

    return "otpauth://totp/%s:%s?%s" % (issuer, device.user.username, urlencode(query))


class OTPTimeStageView(FormView, StageView):

    form_class = SetupForm

    def get_form_kwargs(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs(**kwargs)
        device: TOTPDevice = self.request.session[SESSION_TOTP_DEVICE]
        kwargs["device"] = device
        kwargs["qr_code"] = self._get_qr_code(device)
        return kwargs

    def _get_qr_code(self, device: TOTPDevice) -> str:
        """Get QR Code SVG as string based on `device`"""
        url = otp_auth_url(device)
        qr_code = QRCode(image_factory=SvgFillImage)
        qr_code.add_data(url)
        return force_text(ET.tostring(qr_code.make_image().get_image()))

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        stage: OTPTimeStage = self.executor.current_stage

        if SESSION_TOTP_DEVICE not in self.request.session:
            device = TOTPDevice(user=user, confirmed=True, digits=stage.digits)

            self.request.session[SESSION_TOTP_DEVICE] = device
        return super().get(request, *args, **kwargs)

    def form_valid(self, form: SetupForm) -> HttpResponse:
        """Verify OTP Token"""
        device: TOTPDevice = self.request.session[SESSION_TOTP_DEVICE]
        device.save()
        del self.request.session[SESSION_TOTP_DEVICE]
        return self.executor.stage_ok()
