"""GitLab Processor"""

from passbook.saml_idp.base import Processor


class GitLabProcessor(Processor):
    """GitLab Response Handler Processor for testing against django-saml2-sp."""

    def _determine_audience(self):
        self._audience = self._remote.acs_url.replace('/users/auth/saml/callback', '')
