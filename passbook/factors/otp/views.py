"""passbook OTP Views"""
from base64 import b32encode
from binascii import unhexlify

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views import View
from django.views.generic import FormView, TemplateView
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice
from qrcode import make
from qrcode.image.svg import SvgPathImage
from structlog import get_logger

from passbook.audit.models import Event, EventAction
from passbook.factors.otp.forms import OTPSetupForm
from passbook.factors.otp.utils import otpauth_url
from passbook.lib.boilerplate import NeverCacheMixin
from passbook.lib.config import CONFIG

OTP_SESSION_KEY = 'passbook_factors_otp_key'
OTP_SETTING_UP_KEY = 'passbook_factors_otp_setup'
LOGGER = get_logger()

class UserSettingsView(LoginRequiredMixin, TemplateView):
    """View for user settings to control OTP"""

    template_name = 'otp/user_settings.html'

    # TODO: Check if OTP Factor exists and applies to user
    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        static = StaticDevice.objects.filter(user=self.request.user, confirmed=True)
        if static.exists():
            kwargs['static_tokens'] = StaticToken.objects.filter(device=static.first()) \
                                        .order_by('token')
        totp_devices = TOTPDevice.objects.filter(user=self.request.user, confirmed=True)
        kwargs['state'] = totp_devices.exists() and static.exists()
        return kwargs

class DisableView(LoginRequiredMixin, View):
    """Disable TOTP for user"""

    def get(self, request, *args, **kwargs):
        """Delete all the devices for user"""
        static = get_object_or_404(StaticDevice, user=request.user, confirmed=True)
        static_tokens = StaticToken.objects.filter(device=static).order_by('token')
        totp = TOTPDevice.objects.filter(user=request.user, confirmed=True)
        static.delete()
        totp.delete()
        for token in static_tokens:
            token.delete()
        messages.success(request, 'Successfully disabled OTP')
        # Create event with email notification
        Event.new(EventAction.CUSTOM, message='User disabled OTP.').from_http(request)
        return redirect(reverse('passbook_factors_otp:otp-user-settings'))

class EnableView(LoginRequiredMixin, FormView):
    """View to set up OTP"""

    title = _('Set up OTP')
    form_class = OTPSetupForm
    template_name = 'login/form.html'

    totp_device = None
    static_device = None

    # TODO: Check if OTP Factor exists and applies to user
    def get_context_data(self, **kwargs):
        kwargs['config'] = CONFIG.y('passbook')
        kwargs['is_login'] = True
        kwargs['title'] = _('Configure OTP')
        kwargs['primary_action'] = _('Setup')
        return super().get_context_data(**kwargs)

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if user has TOTP setup already
        finished_totp_devices = TOTPDevice.objects.filter(user=request.user, confirmed=True)
        finished_static_devices = StaticDevice.objects.filter(user=request.user, confirmed=True)
        if finished_totp_devices.exists() and finished_static_devices.exists():
            messages.error(request, _('You already have TOTP enabled!'))
            del request.session[OTP_SETTING_UP_KEY]
            return redirect('passbook_factors_otp:otp-user-settings')
        request.session[OTP_SETTING_UP_KEY] = True
        # Check if there's an unconfirmed device left to set up
        totp_devices = TOTPDevice.objects.filter(user=request.user, confirmed=False)
        if not totp_devices.exists():
            # Create new TOTPDevice and save it, but not confirm it
            self.totp_device = TOTPDevice(user=request.user, confirmed=False)
            self.totp_device.save()
        else:
            self.totp_device = totp_devices.first()

        # Check if we have a static device already
        static_devices = StaticDevice.objects.filter(user=request.user, confirmed=False)
        if not static_devices.exists():
            # Create new static device and some codes
            self.static_device = StaticDevice(user=request.user, confirmed=False)
            self.static_device.save()
            # Create 9 tokens and save them
            # TODO: Send static tokens via E-Mail
            for _counter in range(0, 9):
                token = StaticToken(device=self.static_device, token=StaticToken.random_token())
                token.save()
        else:
            self.static_device = static_devices.first()

        # Somehow convert the generated key to base32 for the QR code
        rawkey = unhexlify(self.totp_device.key.encode('ascii'))
        request.session[OTP_SESSION_KEY] = b32encode(rawkey).decode("utf-8")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class=form_class)
        form.device = self.totp_device
        form.fields['qr_code'].initial = reverse('passbook_factors_otp:otp-qr')
        tokens = [(x.token, x.token) for x in self.static_device.token_set.all()]
        form.fields['tokens'].choices = tokens
        return form

    def form_valid(self, form):
        # Save device as confirmed
        LOGGER.debug("Saved OTP Devices")
        self.totp_device.confirmed = True
        self.totp_device.save()
        self.static_device.confirmed = True
        self.static_device.save()
        del self.request.session[OTP_SETTING_UP_KEY]
        Event.new(EventAction.CUSTOM, message='User enabled OTP.').from_http(self.request)
        return redirect('passbook_factors_otp:otp-user-settings')

class QRView(NeverCacheMixin, View):
    """View returns an SVG image with the OTP token information"""

    def get(self, request: HttpRequest) -> HttpResponse:
        """View returns an SVG image with the OTP token information"""
        # Get the data from the session
        try:
            key = request.session[OTP_SESSION_KEY]
        except KeyError:
            raise Http404

        url = otpauth_url(accountname=request.user.username, secret=key)
        # Make and return QR code
        img = make(url, image_factory=SvgPathImage)
        resp = HttpResponse(content_type='image/svg+xml; charset=utf-8')
        img.save(resp)
        return resp
