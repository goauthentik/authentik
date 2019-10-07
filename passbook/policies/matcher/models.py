"""user field matcher models"""
import re

from django.db import models
from django.utils.translation import gettext as _
from structlog import get_logger

from passbook.core.models import Policy
from passbook.policies.struct import PolicyRequest, PolicyResult

LOGGER = get_logger()

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

    form = 'passbook.policies.matcher.forms.FieldMatcherPolicyForm'

    def __str__(self):
        description = f"{self.name}, user.{self.user_field} {self.match_action} '{self.value}'"
        if self.name:
            description = f"{self.name}: {description}"
        return description

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if user instance passes this role"""
        if not hasattr(request.user, self.user_field):
            raise ValueError("Field does not exist")
        user_field_value = getattr(request.user, self.user_field, None)
        LOGGER.debug("Checking field", value=user_field_value,
                     action=self.match_action, should_be=self.value)
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
        return PolicyResult(passes)

    class Meta:

        verbose_name = _('Field matcher Policy')
        verbose_name_plural = _('Field matcher Policies')
