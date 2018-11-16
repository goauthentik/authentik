"""
Shib Processor
"""

from supervisr.mod.auth.saml.idp.base import Processor


class ShibProcessor(Processor):
    """
    Shib-specific Processor
    """

    def _determine_audience(self):
        """
        Determines the _audience.
        """
        self._audience = "https://sp.testshib.org/shibboleth-sp"
