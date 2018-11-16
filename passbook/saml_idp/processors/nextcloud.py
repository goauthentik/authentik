"""
NextCloud Processor
"""
from supervisr.mod.auth.saml.idp.base import Processor


class NextCloudProcessor(Processor):
    """
    Nextcloud SAML 2.0 AuthnRequest to Response Handler Processor.
    """

    def _determine_audience(self):
        # Nextcloud expects an audience in this format
        # https://<host>/index.php/apps/user_saml/saml/metadata
        self._audience = self._remote.acs_url.replace('acs', 'metadata')
