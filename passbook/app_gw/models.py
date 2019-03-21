"""passbook app_gw models"""
import re

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Policy, PropertyMapping, Provider


class ApplicationGatewayProvider(Provider):
    """Virtual server which proxies requests to any hostname in server_name to upstream"""

    server_name = ArrayField(models.TextField())
    upstream = ArrayField(models.TextField())
    enabled = models.BooleanField(default=True)

    authentication_header = models.TextField(default='X-Remote-User')
    default_content_type = models.TextField(default='application/octet-stream')
    upstream_ssl_verification = models.BooleanField(default=True)

    form = 'passbook.app_gw.forms.ApplicationGatewayProviderForm'

    @property
    def name(self):
        """since this model has no name property, return a joined list of server_names as name"""
        return ', '.join(self.server_name)

    def __str__(self):
        return "Application Gateway %s" % ', '.join(self.server_name)

    class Meta:

        verbose_name = _('Application Gateway Provider')
        verbose_name_plural = _('Application Gateway Providers')


class RewriteRule(PropertyMapping):
    """Rewrite requests matching `match` with `replacement`, if all polcies in `conditions` apply"""

    REDIRECT_INTERNAL = 'internal'
    REDIRECT_PERMANENT = 301
    REDIRECT_FOUND = 302

    REDIRECTS = (
        (REDIRECT_INTERNAL, _('Internal')),
        (REDIRECT_PERMANENT, _('Moved Permanently')),
        (REDIRECT_FOUND, _('Found')),
    )

    match = models.TextField()
    halt = models.BooleanField(default=False)
    conditions = models.ManyToManyField(Policy, blank=True)
    replacement = models.TextField() # python formatted strings, use {match.1}
    redirect = models.CharField(max_length=50, choices=REDIRECTS)

    form = 'passbook.app_gw.forms.RewriteRuleForm'

    _matcher = None

    @property
    def compiled_matcher(self):
        """Cache the compiled regex in memory"""
        if not self._matcher:
            self._matcher = re.compile(self.match)
        return self._matcher

    def __str__(self):
        return "Rewrite Rule %s" % self.name

    class Meta:

        verbose_name = _('Rewrite Rule')
        verbose_name_plural = _('Rewrite Rules')
