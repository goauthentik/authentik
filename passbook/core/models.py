"""passbook core models"""
import re
from datetime import timedelta
from logging import getLogger
from random import SystemRandom
from time import sleep
from typing import Tuple, Union
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField, HStoreField
from django.db import models
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext as _
from model_utils.managers import InheritanceManager

from passbook.core.signals import password_changed
from passbook.lib.models import CreatedUpdatedModel, UUIDModel

LOGGER = getLogger(__name__)


def default_nonce_duration():
    """Default duration a Nonce is valid"""
    return now() + timedelta(hours=4)

class Group(UUIDModel):
    """Custom Group model which supports a basic hierarchy"""

    name = models.CharField(_('name'), max_length=80)
    parent = models.ForeignKey('Group', blank=True, null=True,
                               on_delete=models.SET_NULL, related_name='children')
    tags = HStoreField(default=dict)

    def __str__(self):
        return "Group %s" % self.name

    class Meta:

        unique_together = (('name', 'parent',),)

class User(AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    name = models.TextField()

    sources = models.ManyToManyField('Source', through='UserSourceConnection')
    applications = models.ManyToManyField('Application')
    groups = models.ManyToManyField('Group')
    password_change_date = models.DateTimeField(auto_now_add=True)

    def set_password(self, password):
        if self.pk:
            password_changed.send(sender=self, user=self, password=password)
        self.password_change_date = now()
        return super().set_password(password)

class Provider(models.Model):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    property_mappings = models.ManyToManyField('PropertyMapping', default=None, blank=True)

    objects = InheritanceManager()

    # This class defines no field for easier inheritance
    def __str__(self):
        if hasattr(self, 'name'):
            return getattr(self, 'name')
        return super().__str__()

class PolicyModel(UUIDModel, CreatedUpdatedModel):
    """Base model which can have policies applied to it"""

    policies = models.ManyToManyField('Policy', blank=True)

class Factor(PolicyModel):
    """Authentication factor, multiple instances of the same Factor can be used"""

    name = models.TextField()
    slug = models.SlugField(unique=True)
    order = models.IntegerField()
    enabled = models.BooleanField(default=True)

    objects = InheritanceManager()
    type = ''
    form = ''

    def has_user_settings(self):
        """Entrypoint to integrate with User settings. Can either return False if no
        user settings are available, or a tuple or string, string, string where the first string
        is the name the item has, the second string is the icon and the third is the view-name."""
        return False

    def __str__(self):
        return "Factor %s" % self.slug

class PasswordFactor(Factor):
    """Password-based Django-backend Authentication Factor"""

    backends = ArrayField(models.TextField())
    password_policies = models.ManyToManyField('Policy', blank=True)

    type = 'passbook.core.auth.factors.password.PasswordFactor'
    form = 'passbook.core.forms.factors.PasswordFactorForm'

    def has_user_settings(self):
        return _('Change Password'), 'pficon-key', 'passbook_core:user-change-password'

    def password_passes(self, user: User) -> bool:
        """Return true if user's password passes, otherwise False or raise Exception"""
        for policy in self.policies.all():
            if not policy.passes(user):
                return False
        return True

    def __str__(self):
        return "Password Factor %s" % self.slug

    class Meta:

        verbose_name = _('Password Factor')
        verbose_name_plural = _('Password Factors')

class DummyFactor(Factor):
    """Dummy factor, mostly used to debug"""

    type = 'passbook.core.auth.factors.dummy.DummyFactor'
    form = 'passbook.core.forms.factors.DummyFactorForm'

    def __str__(self):
        return "Dummy Factor %s" % self.slug

    class Meta:

        verbose_name = _('Dummy Factor')
        verbose_name_plural = _('Dummy Factors')

class Application(PolicyModel):
    """Every Application which uses passbook for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField()
    slug = models.SlugField()
    launch_url = models.URLField(null=True, blank=True)
    icon_url = models.TextField(null=True, blank=True)
    provider = models.OneToOneField('Provider', null=True, blank=True,
                                    default=None, on_delete=models.SET_DEFAULT)
    skip_authorization = models.BooleanField(default=False)

    objects = InheritanceManager()

    def get_provider(self):
        """Get casted provider instance"""
        if not self.provider:
            return None
        return Provider.objects.get_subclass(pk=self.provider.pk)

    def __str__(self):
        return self.name

class Source(PolicyModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField()
    slug = models.SlugField()
    form = '' # ModelForm-based class ued to create/edit instance
    enabled = models.BooleanField(default=True)

    objects = InheritanceManager()

    @property
    def is_link(self):
        """Return true if Source should get a link on the login page"""
        return False

    @property
    def get_login_button(self):
        """Return a tuple of URL, Icon name and Name"""
        raise NotImplementedError

    @property
    def additional_info(self):
        """Return additional Info, such as a callback URL. Show in the administration interface."""
        return None

    def has_user_settings(self):
        """Entrypoint to integrate with User settings. Can either return False if no
        user settings are available, or a tuple or string, string, string where the first string
        is the name the item has, the second string is the icon and the third is the view-name."""
        return False

    def __str__(self):
        return self.name

class UserSourceConnection(CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:

        unique_together = (('user', 'source'),)

class Policy(UUIDModel, CreatedUpdatedModel):
    """Policies which specify if a user is authorized to use an Application. Can be overridden by
    other types to add other fields, more logic, etc."""

    ACTION_ALLOW = 'allow'
    ACTION_DENY = 'deny'
    ACTIONS = (
        (ACTION_ALLOW, ACTION_ALLOW),
        (ACTION_DENY, ACTION_DENY),
    )

    name = models.TextField(blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    negate = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    timeout = models.IntegerField(default=30)

    objects = InheritanceManager()

    def __str__(self):
        if self.name:
            return self.name
        return "%s action %s" % (self.name, self.action)

    def passes(self, user: User) -> Union[bool, Tuple[bool, str]]:
        """Check if user instance passes this policy"""
        raise NotImplementedError()

class FieldMatcherPolicy(Policy):
    """Policy which checks if a field of the User model matches/doesn't match a
    certain pattern"""

    MATCH_STARTSWITH = 'startswith'
    MATCH_ENDSWITH = 'endswith'
    MATCH_CONTAINS = 'contains'
    MATCH_REGEXP = 'regexp'
    MATCH_EXACT = 'exact'

    MATCHES = (
        (MATCH_STARTSWITH, _('Starts with')),
        (MATCH_ENDSWITH, _('Ends with')),
        (MATCH_CONTAINS, _('Contains')),
        (MATCH_REGEXP, _('Regexp')),
        (MATCH_EXACT, _('Exact')),
    )

    USER_FIELDS = (
        ('username', _('Username'),),
        ('name', _('Name'),),
        ('email', _('E-Mail'),),
        ('is_staff', _('Is staff'),),
        ('is_active', _('Is active'),),
        ('data_joined', _('Date joined'),),
    )

    user_field = models.TextField(choices=USER_FIELDS)
    match_action = models.CharField(max_length=50, choices=MATCHES)
    value = models.TextField()

    form = 'passbook.core.forms.policies.FieldMatcherPolicyForm'

    def __str__(self):
        description = "%s, user.%s %s '%s'" % (self.name, self.user_field,
                                               self.match_action, self.value)
        if self.name:
            description = "%s: %s" % (self.name, description)
        return description

    def passes(self, user: User) -> Union[bool, Tuple[bool, str]]:
        """Check if user instance passes this role"""
        if not hasattr(user, self.user_field):
            raise ValueError("Field does not exist")
        user_field_value = getattr(user, self.user_field, None)
        LOGGER.debug("Checked '%s' %s with '%s'...",
                     user_field_value, self.match_action, self.value)
        passes = False
        if self.match_action == FieldMatcherPolicy.MATCH_STARTSWITH:
            passes = user_field_value.startswith(self.value)
        if self.match_action == FieldMatcherPolicy.MATCH_ENDSWITH:
            passes = user_field_value.endswith(self.value)
        if self.match_action == FieldMatcherPolicy.MATCH_CONTAINS:
            passes = self.value in user_field_value
        if self.match_action == FieldMatcherPolicy.MATCH_REGEXP:
            pattern = re.compile(self.value)
            passes = bool(pattern.match(user_field_value))
        if self.match_action == FieldMatcherPolicy.MATCH_EXACT:
            passes = user_field_value == self.value

        LOGGER.debug("User got '%r'", passes)
        return passes

    class Meta:

        verbose_name = _('Field matcher Policy')
        verbose_name_plural = _('Field matcher Policies')

class PasswordPolicy(Policy):
    """Policy to make sure passwords have certain properties"""

    amount_uppercase = models.IntegerField(default=0)
    amount_lowercase = models.IntegerField(default=0)
    amount_symbols = models.IntegerField(default=0)
    length_min = models.IntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")
    error_message = models.TextField()

    form = 'passbook.core.forms.policies.PasswordPolicyForm'

    def passes(self, user: User) -> Union[bool, Tuple[bool, str]]:
        # Only check if password is being set
        if not hasattr(user, '__password__'):
            return True
        password = getattr(user, '__password__')

        filter_regex = r''
        if self.amount_lowercase > 0:
            filter_regex += r'[a-z]{%d,}' % self.amount_lowercase
        if self.amount_uppercase > 0:
            filter_regex += r'[A-Z]{%d,}' % self.amount_uppercase
        if self.amount_symbols > 0:
            filter_regex += r'[%s]{%d,}' % (self.symbol_charset, self.amount_symbols)
        result = bool(re.compile(filter_regex).match(password))
        LOGGER.debug("User got %r", result)
        if not result:
            return result, self.error_message
        return result

    class Meta:

        verbose_name = _('Password Policy')
        verbose_name_plural = _('Password Policies')


class WebhookPolicy(Policy):
    """Policy that asks webhook"""

    METHOD_GET = 'GET'
    METHOD_POST = 'POST'
    METHOD_PATCH = 'PATCH'
    METHOD_DELETE = 'DELETE'
    METHOD_PUT = 'PUT'

    METHODS = (
        (METHOD_GET, METHOD_GET),
        (METHOD_POST, METHOD_POST),
        (METHOD_PATCH, METHOD_PATCH),
        (METHOD_DELETE, METHOD_DELETE),
        (METHOD_PUT, METHOD_PUT),
    )

    url = models.URLField()
    method = models.CharField(max_length=10, choices=METHODS)
    json_body = models.TextField()
    json_headers = models.TextField()
    result_jsonpath = models.TextField()
    result_json_value = models.TextField()

    form = 'passbook.core.forms.policies.WebhookPolicyForm'

    def passes(self, user: User):
        """Call webhook asynchronously and report back"""
        raise NotImplementedError()

    class Meta:

        verbose_name = _('Webhook Policy')
        verbose_name_plural = _('Webhook Policies')

class DebugPolicy(Policy):
    """Policy used for debugging the PolicyEngine. Returns a fixed result,
    but takes a random time to process."""

    result = models.BooleanField(default=False)
    wait_min = models.IntegerField(default=5)
    wait_max = models.IntegerField(default=30)

    form = 'passbook.core.forms.policies.DebugPolicyForm'

    def passes(self, user: User):
        """Wait random time then return result"""
        wait = SystemRandom().randrange(self.wait_min, self.wait_max)
        LOGGER.debug("Policy '%s' waiting for %ds", self.name, wait)
        sleep(wait)
        return self.result, 'Debugging'

    class Meta:

        verbose_name = _('Debug Policy')
        verbose_name_plural = _('Debug Policies')

class GroupMembershipPolicy(Policy):
    """Policy to check if the user is member in a certain group"""

    group = models.ForeignKey('Group', on_delete=models.CASCADE)

    form = 'passbook.core.forms.policies.GroupMembershipPolicyForm'

    def passes(self, user: User) -> Union[bool, Tuple[bool, str]]:
        return self.group.user_set.filter(pk=user.pk).exists()

    class Meta:

        verbose_name = _('Group Membership Policy')
        verbose_name_plural = _('Group Membership Policies')

class Invitation(UUIDModel):
    """Single-use invitation link"""

    created_by = models.ForeignKey('User', on_delete=models.CASCADE)
    expires = models.DateTimeField(default=None, blank=True, null=True)
    fixed_username = models.TextField(blank=True, default=None)
    fixed_email = models.TextField(blank=True, default=None)
    needs_confirmation = models.BooleanField(default=True)

    @property
    def link(self):
        """Get link to use invitation"""
        return reverse_lazy('passbook_core:auth-sign-up') + '?invitation=%s' % self.uuid

    def __str__(self):
        return "Invitation %s created by %s" % (self.uuid, self.created_by)

    class Meta:

        verbose_name = _('Invitation')
        verbose_name_plural = _('Invitations')

class Nonce(UUIDModel):
    """One-time link for password resets/sign-up-confirmations"""

    expires = models.DateTimeField(default=default_nonce_duration)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    expiring = models.BooleanField(default=True)

    def __str__(self):
        return "Nonce %s (expires=%s)" % (self.uuid.hex, self.expires)

    class Meta:

        verbose_name = _('Nonce')
        verbose_name_plural = _('Nonces')

class PropertyMapping(UUIDModel):
    """User-defined key -> x mapping which can be used by providers to expose extra data."""

    name = models.TextField()

    form = ''
    objects = InheritanceManager()

    def __str__(self):
        return "Property Mapping %s" % self.name

    class Meta:

        verbose_name = _('Property Mapping')
        verbose_name_plural = _('Property Mappings')
