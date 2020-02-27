"""passbook saml provider types"""
from dataclasses import dataclass


@dataclass
class SAMLResponseParams:
    """Class to keep track of SAML Response Parameters"""

    acs_url: str
    saml_response: str
    relay_state: str
