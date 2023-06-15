"""Enterprise license policies"""
from typing import Optional

from rest_framework.serializers import BaseSerializer

from authentik.core.models import User, UserTypes
from authentik.enterprise.models import LicenseKey
from authentik.policies.models import Policy
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.policies.views import PolicyAccessView


class EnterprisePolicy(Policy):
    """Check that a user is correctly licensed for the request"""

    @property
    def component(self) -> str:
        return ""

    @property
    def serializer(self) -> type[BaseSerializer]:
        raise NotImplementedError

    def passes(self, request: PolicyRequest) -> PolicyResult:
        if not LicenseKey.get_total().is_valid():
            return PolicyResult(False)
        if request.user.type != UserTypes.DEFAULT:
            return PolicyResult(False)
        return PolicyResult(True)


class EnterprisePolicyAccessView(PolicyAccessView):
    """PolicyAccessView which also checks enterprise licensing"""

    def user_has_access(self, user: Optional[User] = None) -> PolicyResult:
        user = user or self.request.user
        request = PolicyRequest(user)
        request.http_request = self.request
        result = super().user_has_access(user)
        enterprise_result = EnterprisePolicy().passes(request)
        if not enterprise_result.passing:
            return enterprise_result
        return result

    def resolve_provider_application(self):
        raise NotImplementedError
