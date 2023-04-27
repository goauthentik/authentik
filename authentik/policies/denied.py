"""policy http response"""
from typing import Any, Optional

from django.http.request import HttpRequest
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from authentik.core.models import USER_ATTRIBUTE_DEBUG
from authentik.policies.types import PolicyResult


class AccessDeniedResponse(TemplateResponse):
    """Response used for access denied messages. Can optionally show an error message,
    and if the user is a superuser or has user_debug enabled, shows a policy result."""

    title: str

    error_message: Optional[str] = None
    policy_result: Optional[PolicyResult] = None

    def __init__(self, request: HttpRequest, template="policies/denied.html") -> None:
        super().__init__(request, template)
        self.title = _("Access denied")

    def resolve_context(self, context: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if not context:
            context = {}
        context["title"] = self.title
        if self.error_message:
            context["error"] = self.error_message
        # Only show policy result if user is authenticated and
        # either superuser or has USER_ATTRIBUTE_DEBUG set
        if self.policy_result:
            if self._request.user and self._request.user.is_authenticated:
                if self._request.user.is_superuser or self._request.user.group_attributes(
                    self._request
                ).get(USER_ATTRIBUTE_DEBUG, False):
                    context["policy_result"] = self.policy_result
        context["cancel"] = reverse("authentik_flows:cancel")
        return context
