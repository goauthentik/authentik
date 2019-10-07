"""sso models"""
from django.utils.translation import gettext as _

from passbook.core.models import Policy
from passbook.policies.struct import PolicyRequest, PolicyResult


class SSOLoginPolicy(Policy):
    """Policy that applies to users that have authenticated themselves through SSO"""

    form = 'passbook.policies.sso.forms.SSOLoginPolicyForm'

    def passes(self, request: PolicyRequest) -> PolicyResult:
        """Check if user instance passes this policy"""
        from passbook.factors.view import AuthenticationView
        is_sso_login = request.user.session.get(AuthenticationView.SESSION_IS_SSO_LOGIN, False)
        return PolicyResult(is_sso_login)

    class Meta:

        verbose_name = _('SSO Login Policy')
        verbose_name_plural = _('SSO Login Policies')
