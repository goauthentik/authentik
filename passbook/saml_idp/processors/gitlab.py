"""
GitLab Processor
"""

from supervisr.mod.auth.saml.idp.base import Processor


class GitLabProcessor(Processor):
    """
    GitLab Response Handler Processor for testing against django-saml2-sp.
    """

    def _determine_audience(self):
        # Nextcloud expects an audience in this format
        # https://<host>
        self._audience = self._remote.acs_url.replace('/users/auth/saml/callback', '')
