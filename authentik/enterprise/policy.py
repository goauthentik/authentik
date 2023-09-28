"""Enterprise license policies"""
from typing import Optional

from authentik.core.models import User, UserTypes
from authentik.enterprise.models import LicenseKey
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.policies.views import PolicyAccessView


class EnterprisePolicyAccessView(PolicyAccessView):
    """PolicyAccessView which also checks enterprise licensing"""

    def check_license(self):
        """Check license"""
        if not LicenseKey.get_total().is_valid():
            return False
        if self.request.user.type != UserTypes.INTERNAL:
            return False
        return True

    def user_has_access(self, user: Optional[User] = None) -> PolicyResult:
        user = user or self.request.user
        request = PolicyRequest(user)
        request.http_request = self.request
        result = super().user_has_access(user)
        enterprise_result = self.check_license()
        if not enterprise_result:
            return enterprise_result
        return result

    def resolve_provider_application(self):
        raise NotImplementedError
