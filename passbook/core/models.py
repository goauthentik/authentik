"""passbook core models"""
import re
from logging import getLogger

import reversion
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _
from model_utils.managers import InheritanceManager

from passbook.lib.models import CreatedUpdatedModel, UUIDModel

LOGGER = getLogger(__name__)

@reversion.register()
class User(AbstractUser):
    """Custom User model to allow easier adding o f user-based settings"""

    sources = models.ManyToManyField('Source', through='UserSourceConnection')
    applications = models.ManyToManyField('Application')

@reversion.register()
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

@reversion.register()
class Application(RuleModel):
    """Every Application which uses passbook for authentication/identification/authorization
    needs an Application record. Other authentication types can subclass this Model to
    add custom fields and other properties"""

    name = models.TextField()
    launch_url = models.URLField(null=True, blank=True)
    icon_url = models.TextField(null=True, blank=True)
    provider = models.OneToOneField('Provider', null=True,
                                    default=None, on_delete=models.SET_DEFAULT)
    skip_authorization = models.BooleanField(default=False)

    objects = InheritanceManager()

    def user_is_authorized(self, user: User) -> bool:
        """Check if user is authorized to use this application"""
        raise NotImplementedError()

    def __str__(self):
        return self.name

@reversion.register()
class Source(RuleModel):
    """Base Authentication source, i.e. an OAuth Provider, SAML Remote or LDAP Server"""

    name = models.TextField()
    slug = models.SlugField()
    form = '' # ModelForm-based class ued to create/edit instance
    enabled = models.BooleanField(default=True)

    objects = InheritanceManager()

    def __str__(self):
        return self.name

@reversion.register()
class UserSourceConnection(CreatedUpdatedModel):
    """Connection between User and Source."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:

        unique_together = (('user', 'source'),)

@reversion.register()
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

@reversion.register()
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

    user_field = models.TextField()
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
            passes = pattern.match(user_field_value)
        if self.negate:
            passes = not passes
        LOGGER.debug("User got '%r'", passes)
        return passes

    class Meta:

        verbose_name = _('Field matcher Rule')
        verbose_name_plural = _('Field matcher Rules')
