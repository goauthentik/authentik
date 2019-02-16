"""passbook core models"""
import re
from logging import getLogger
from random import SystemRandom
from time import sleep
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from model_utils.managers import InheritanceManager

from passbook.lib.models import CreatedUpdatedModel, UUIDModel

LOGGER = getLogger(__name__)

class Group(UUIDModel):
    """Custom Group model which supports a basic hierarchy"""

    name = models.CharField(_('name'), max_length=80)
    parent = models.ForeignKey('Group', blank=True, null=True,
                               on_delete=models.SET_NULL, related_name='children')
    extra_data = models.TextField(blank=True)

    def __str__(self):
        return "Group %s" % self.name

    class Meta:

        unique_together = (('name', 'parent',),)

class User(AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    uuid = models.UUIDField(default=uuid4, editable=False)
    sources = models.ManyToManyField('Source', through='UserSourceConnection')
    applications = models.ManyToManyField('Application')
    groups = models.ManyToManyField('Group')

class Provider(models.Model):
    """Application-independent Provider instance. For example SAML2 Remote, OAuth2 Application"""

    objects = InheritanceManager()

    # This class defines no field for easier inheritance
    def __str__(self):
        if hasattr(self, 'name'):
            return getattr(self, 'name')
        return super().__str__()

class RuleModel(UUIDModel, CreatedUpdatedModel):
    """Base model which can have rules applied to it"""

    rules = models.ManyToManyField('Rule', blank=True)

    def passes(self, user: User) -> bool:
        """Return true if user passes, otherwise False or raise Exception"""
        for rule in self.rules:
            if not rule.passes(user):
                return False
        return True

class Factor(RuleModel):
    """Authentication factor, multiple instances of the same Factor can be used"""

    name = models.TextField()
    slug = models.SlugField(unique=True)
    order = models.IntegerField()
    type = models.TextField(unique=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return "Factor %s" % self.slug

class Application(RuleModel):
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

    def user_is_authorized(self, user: User) -> bool:
        """Check if user is authorized to use this application"""
        from passbook.core.rules import RuleEngine
        return RuleEngine(self.rules.all()).for_user(user).result

    def __str__(self):
        return self.name

class Source(RuleModel):
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
    def get_url(self):
        """Return URL used for logging in"""
        raise NotImplementedError

    def __str__(self):
        return self.name

class UserSourceConnection(CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:

        unique_together = (('user', 'source'),)

class Rule(UUIDModel, CreatedUpdatedModel):
    """Rules which specify if a user is authorized to use an Application. Can be overridden by
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

    objects = InheritanceManager()

    def __str__(self):
        if self.name:
            return self.name
        return "%s action %s" % (self.name, self.action)

    def passes(self, user: User) -> bool:
        """Check if user instance passes this rule"""
        raise NotImplementedError()

class FieldMatcherRule(Rule):
    """Rule which checks if a field of the User model matches/doesn't match a
    certain pattern"""

    MATCH_STARTSWITH = 'startswith'
    MATCH_ENDSWITH = 'endswith'
    MATCH_CONTAINS = 'contains'
    MATCH_REGEXP = 'regexp'
    MATCH_EXACT = 'exact'

    MATCHES = (
        (MATCH_STARTSWITH, _('Starts with')),
        (MATCH_ENDSWITH, _('Ends with')),
        (MATCH_ENDSWITH, _('Contains')),
        (MATCH_REGEXP, _('Regexp')),
        (MATCH_EXACT, _('Exact')),
    )

    USER_FIELDS = (
        ('username', _('Username'),),
        ('first_name', _('First Name'),),
        ('last_name', _('Last Name'),),
        ('email', _('E-Mail'),),
        ('is_staff', _('Is staff'),),
        ('is_active', _('Is active'),),
        ('data_joined', _('Date joined'),),
    )

    user_field = models.TextField(choices=USER_FIELDS)
    match_action = models.CharField(max_length=50, choices=MATCHES)
    value = models.TextField()

    form = 'passbook.core.forms.rules.FieldMatcherRuleForm'

    def __str__(self):
        description = "%s, user.%s %s '%s'" % (self.name, self.user_field,
                                               self.match_action, self.value)
        if self.name:
            description = "%s: %s" % (self.name, description)
        return description

    def passes(self, user: User) -> bool:
        """Check if user instance passes this role"""
        if not hasattr(user, self.user_field):
            raise ValueError("Field does not exist")
        user_field_value = getattr(user, self.user_field, None)
        LOGGER.debug("Checked '%s' %s with '%s'...",
                     user_field_value, self.match_action, self.value)
        passes = False
        if self.match_action == FieldMatcherRule.MATCH_STARTSWITH:
            passes = user_field_value.startswith(self.value)
        if self.match_action == FieldMatcherRule.MATCH_ENDSWITH:
            passes = user_field_value.endswith(self.value)
        if self.match_action == FieldMatcherRule.MATCH_CONTAINS:
            passes = self.value in user_field_value
        if self.match_action == FieldMatcherRule.MATCH_REGEXP:
            pattern = re.compile(self.value)
            passes = bool(pattern.match(user_field_value))
        if self.negate:
            passes = not passes
        LOGGER.debug("User got '%r'", passes)
        return passes

    class Meta:

        verbose_name = _('Field matcher Rule')
        verbose_name_plural = _('Field matcher Rules')

class PasswordPolicyRule(Rule):
    """Rule to make sure passwords have certain properties"""

    amount_uppercase = models.IntegerField(default=0)
    amount_lowercase = models.IntegerField(default=0)
    amount_symbols = models.IntegerField(default=0)
    length_min = models.IntegerField(default=0)
    symbol_charset = models.TextField(default=r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ")

    form = 'passbook.core.forms.rules.PasswordPolicyRuleForm'

    def passes(self, user: User) -> bool:
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
        return result

    class Meta:

        verbose_name = _('Password Policy Rule')
        verbose_name_plural = _('Password Policy Rules')


class WebhookRule(Rule):
    """Rule that asks webhook"""

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

    form = 'passbook.core.forms.rules.WebhookRuleForm'

    def passes(self, user: User):
        """Call webhook asynchronously and report back"""
        raise NotImplementedError()

    class Meta:

        verbose_name = _('Webhook Rule')
        verbose_name_plural = _('Webhook Rules')

class DebugRule(Rule):
    """Rule used for debugging the RuleEngine. Returns a fixed result,
    but takes a random time to process."""

    result = models.BooleanField(default=False)
    wait_min = models.IntegerField(default=5)
    wait_max = models.IntegerField(default=30)

    form = 'passbook.core.forms.rules.DebugRuleForm'

    def passes(self, user: User):
        """Wait random time then return result"""
        wait = SystemRandom().randrange(self.wait_min, self.wait_max)
        LOGGER.debug("Rule '%s' waiting for %ds", self.name, wait)
        sleep(wait)
        return self.result

    class Meta:

        verbose_name = _('Debug Rule')
        verbose_name_plural = _('Debug Rules')

class Invitation(UUIDModel):
    """Single-use invitation link"""

    created_by = models.ForeignKey('User', on_delete=models.CASCADE)
    expires = models.DateTimeField(default=None, blank=True, null=True)
    fixed_username = models.TextField(blank=True, default=None)
    fixed_email = models.TextField(blank=True, default=None)

    @property
    def link(self):
        """Get link to use invitation"""
        return reverse_lazy('passbook_core:auth-sign-up') + '?invitation=%s' % self.uuid

    def __str__(self):
        return "Invitation %s created by %s" % (self.uuid, self.created_by)

    class Meta:

        verbose_name = _('Invitation')
        verbose_name_plural = _('Invitations')
