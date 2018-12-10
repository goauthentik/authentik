"""passbook core authentication forms"""
from logging import getLogger

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from passbook.core.models import User
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)

class LoginForm(forms.Form):
    """Allow users to login"""

    title = _('Log in to your account')
    uid_field = forms.CharField(widget=forms.TextInput(attrs={'placeholder': _('UID')}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': _('Password')}))
    remember_me = forms.BooleanField(required=False)

    def clean_uid_field(self):
        """Validate uid_field after EmailValidator if 'email' is the only selected uid_fields"""
        if CONFIG.y('passbook.uid_fields') == ['email']:
            validate_email(self.cleaned_data.get('uid_field'))
        return self.cleaned_data.get('uid_field')

class SignUpForm(forms.Form):
    """SignUp Form"""

    title = _('Sign Up')
    first_name = forms.CharField(label=_('First Name'),
                                 widget=forms.TextInput(attrs={'placeholder': _('First Name')}))
    last_name = forms.CharField(label=_('Last Name'),
                                widget=forms.TextInput(attrs={'placeholder': _('Last Name')}))
    username = forms.CharField(label=_('Username'),
                               widget=forms.TextInput(attrs={'placeholder': _('Username')}))
    email = forms.EmailField(label=_('E-Mail'),
                             widget=forms.TextInput(attrs={'placeholder': _('E-Mail')}))
    password = forms.CharField(label=_('Password'),
                               widget=forms.PasswordInput(attrs={'placeholder': _('Password')}))
    password_repeat = forms.CharField(label=_('Repeat Password'),
                                      widget=forms.PasswordInput(attrs={
                                          'placeholder': _('Repeat Password')
                                          }))
    # captcha = ReCaptchaField(
    #     required=(not settings.DEBUG and not settings.TEST),
    #     private_key=Setting.get('recaptcha:private'),
    #     public_key=Setting.get('recaptcha:public'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # All fields which have initial data supplied are set to read only
        if 'initial' in kwargs:
            for field, _ in kwargs.get('initial').items():
                self.fields[field].widget.attrs['readonly'] = 'readonly'
        # TODO: Dynamically add captcha here
        # if not Setting.get_bool('recaptcha:enabled'):
        #     self.fields.pop('captcha')

    def clean_username(self):
        """Check if username is used already"""
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            LOGGER.warning("Username %s already exists", username)
            raise ValidationError(_("Username already exists"))
        return username

    def clean_email(self):
        """Check if email is already used in django or other auth sources"""
        email = self.cleaned_data.get('email')
        # Check if user exists already, error early
        if User.objects.filter(email=email).exists():
            LOGGER.debug("email %s exists in django", email)
            raise ValidationError(_("Email already exists"))
        return email

    def clean_password_repeat(self):
        """Check if Password adheres to filter and if passwords matche"""
        # TODO: Password policy? Via Plugin? via Policy?
        # return check_password(self)
        return self.cleaned_data.get('password_repeat')
