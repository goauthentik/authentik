"""Rancher Processor"""
from passbook.saml_idp.base import Processor


class RancherProcessor(Processor):
    """Rancher SAML 2.0 AuthnRequest to Response Handler Processor."""

    def _determine_audience(self):
        # Rancher expects an audience in this format
        # https://<host>/v1-saml/adfs/saml/acs
        self._audience = self._remote.acs_url.replace('acs', 'metadata')
