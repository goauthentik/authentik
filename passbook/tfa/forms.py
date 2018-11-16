"""Supervisr 2FA Forms"""

from django import forms
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

TFA_CODE_VALIDATOR = RegexValidator(r'^[0-9a-z]{6,8}$',
                                    _('Only alpha-numeric characters are allowed.'))


class PictureWidget(forms.widgets.Widget):
    """Widget to render value as img-tag"""

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe("<img src=\"%s\" />" % value) # nosec


class TFAVerifyForm(forms.Form):
    """Simple Form to verify 2FA Code"""
    order = ['code']

    code = forms.CharField(label=_('Code'), validators=[TFA_CODE_VALIDATOR],
                           widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def __init__(self, *args, **kwargs):
        super(TFAVerifyForm, self).__init__(*args, **kwargs)
        # This is a little helper so the field is focused by default
        self.fields['code'].widget.attrs.update({'autofocus': 'autofocus'})


class TFASetupInitForm(forms.Form):
    """Initial 2FA Setup form"""
    title = _('Set up 2FA')
    device = None
    confirmed = False
    qr_code = forms.CharField(widget=PictureWidget, disabled=True, required=False,
                              label=_('Scan this Code with your 2FA App.'))
    code = forms.CharField(label=_('Code'), validators=[TFA_CODE_VALIDATOR])

    def clean_code(self):
        """Check code with new totp device"""
        if self.device is not None:
            if not self.device.verify_token(int(self.cleaned_data.get('code'))) \
                    and not self.confirmed:
                raise forms.ValidationError(_("2FA Code does not match"))
        return self.cleaned_data.get('code')


class TFASetupStaticForm(forms.Form):
    """Static form to show generated static tokens"""
    tokens = forms.MultipleChoiceField(disabled=True, required=False)
