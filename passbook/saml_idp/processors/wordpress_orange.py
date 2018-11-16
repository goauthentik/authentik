"""
WordpressOrange Processor
"""

from supervisr.mod.auth.saml.idp.base import Processor


class WordpressOrangeProcessor(Processor):
    """
    WordpressOrange Response Handler Processor for testing against django-saml2-sp.
    """

    def _determine_audience(self):
        # Orange expects an audience in this format
        # https://<host>/wp-content/plugins/miniorange-saml-20-single-sign-on/
        self._audience = self._remote.acs_url + \
            'wp-content/plugins/miniorange-saml-20-single-sign-on/'
