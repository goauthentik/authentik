"""webhook models"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult


class WebhookPolicy(Policy):
    """Policy that asks webhook"""

    METHOD_GET = "GET"
    METHOD_POST = "POST"
    METHOD_PATCH = "PATCH"
    METHOD_DELETE = "DELETE"
    METHOD_PUT = "PUT"

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

    form = "passbook.policies.webhook.forms.WebhookPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Call webhook asynchronously and report back"""
        raise NotImplementedError()

    class Meta:

        verbose_name = _("Webhook Policy")
        verbose_name_plural = _("Webhook Policies")
