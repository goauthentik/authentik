"""TOTP Setup stage"""
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.utils.encoding import force_str
from django.views.generic import FormView
from django_otp.plugins.otp_totp.models import TOTPDevice
from lxml.etree import tostring  # nosec
from qrcode import QRCode
from qrcode.image.svg import SvgFillImage
from structlog import get_logger

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER
from passbook.flows.stage import StageView
from passbook.stages.otp_time.forms import SetupForm
from passbook.stages.otp_time.models import OTPTimeStage

LOGGER = get_logger()
SESSION_TOTP_DEVICE = "totp_device"


class OTPTimeStageView(FormView, StageView):
    """OTP totp Setup stage"""

    form_class = SetupForm

    def get_form_kwargs(self, **kwargs) -> Dict[str, Any]:
        kwargs = super().get_form_kwargs(**kwargs)
        device: TOTPDevice = self.request.session[SESSION_TOTP_DEVICE]
        kwargs["device"] = device
        kwargs["qr_code"] = self._get_qr_code(device)
        return kwargs

    def _get_qr_code(self, device: TOTPDevice) -> str:
        """Get QR Code SVG as string based on `device`"""
        qr_code = QRCode(image_factory=SvgFillImage)
        qr_code.add_data(device.config_url)
        svg_image = tostring(qr_code.make_image().get_image())
        sr_wrapper = f'<div id="qr" data-otpuri="{device.config_url}">{force_str(svg_image)}</div>'
        return sr_wrapper

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()

        # Currently, this stage only supports one device per user. If the user already
        # has a device, just skip to the next stage
        if TOTPDevice.objects.filter(user=user).exists():
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
