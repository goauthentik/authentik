"""Shibboleth Processor"""

from supervisr.mod.auth.saml.idp.base import Processor


class ShibbolethProcessor(Processor):
    """Shibboleth-specific Processor"""

    def _determine_audience(self):
        """Determines the _audience."""
        self._audience = "https://sp.testshib.org/shibboleth-sp"
