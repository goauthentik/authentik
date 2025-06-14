"""Enterprise license policies"""

from django.utils.translation import gettext_lazy as _

from authentik.core.models import User, UserTypes
from authentik.enterprise.license import LicenseKey
from authentik.policies.types import PolicyRequest, PolicyResult
from authentik.policies.views import PolicyAccessView


class EnterprisePolicyAccessView(PolicyAccessView):
    """PolicyAccessView which also checks enterprise licensing"""

    def check_license(self):
        """Check license"""
        if not LicenseKey.get_total().status().is_valid:
            return PolicyResult(False, _("Enterprise required to access this feature."))
        if self.request.user.type != UserTypes.INTERNAL:
            return PolicyResult(False, _("Feature only accessible for internal users."))
        return PolicyResult(True)

    def user_has_access(self, user: User | None = None) -> PolicyResult:
        user = user or self.request.user
        request = PolicyRequest(user)
        request.http_request = self.request
        result = super().user_has_access(user)
        enterprise_result = self.check_license()
        if not enterprise_result.passing:
            return enterprise_result
        return result

    def resolve_provider_application(self):
        raise NotImplementedError
