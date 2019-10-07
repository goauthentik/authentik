"""passbook OTP Forms"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_otp.models import Device

from passbook.factors.forms import GENERAL_FIELDS
from passbook.factors.otp.models import OTPFactor

OTP_CODE_VALIDATOR = RegexValidator(r'^[0-9a-z]{6,8}$',
                                    _('Only alpha-numeric characters are allowed.'))


class PictureWidget(forms.widgets.Widget):
    """Widget to render value as img-tag"""

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(f'<img src="{value}" />') # nosec


class OTPVerifyForm(forms.Form):
    """Simple Form to verify OTP Code"""
    order = ['code']

    code = forms.CharField(label=_('Code'), validators=[OTP_CODE_VALIDATOR],
                           widget=forms.TextInput(attrs={
                               'autocomplete': 'off',
                               'placeholder': 'Code'
                               }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is a little helper so the field is focused by default
        self.fields['code'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocomplete': 'off'
        })


class OTPSetupForm(forms.Form):
    """OTP Setup form"""
    title = _('Set up OTP')
    device: Device = None
    qr_code = forms.CharField(widget=PictureWidget, disabled=True, required=False,
                              label=_('Scan this Code with your OTP App.'))
    code = forms.CharField(label=_('Code'), validators=[OTP_CODE_VALIDATOR],
                           widget=forms.TextInput(attrs={'placeholder': _('One-Time Password')}))

    tokens = forms.MultipleChoiceField(disabled=True, required=False)

    def clean_code(self):
        """Check code with new otp device"""
        if self.device is not None:
            if not self.device.verify_token(int(self.cleaned_data.get('code'))):
                raise forms.ValidationError(_("OTP Code does not match"))
        return self.cleaned_data.get('code')

class OTPFactorForm(forms.ModelForm):
    """Form to edit OTPFactor instances"""

    class Meta:

        model = OTPFactor
        fields = GENERAL_FIELDS + ['enforced']
        widgets = {
            'name': forms.TextInput(),
            'order': forms.NumberInput(),
            'policies': FilteredSelectMultiple(_('policies'), False)
        }
