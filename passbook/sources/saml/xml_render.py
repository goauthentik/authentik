"""Functions for creating XML output."""
from structlog import get_logger

from passbook.lib.utils.template import render_to_string
from passbook.providers.saml.xml_signing import get_signature_xml

LOGGER = get_logger()


def get_authnrequest_xml(parameters, signed=False):
    """Get AuthN Request XML"""
    # Reset signature.
    params = {}
    params.update(parameters)
    params["AUTHN_REQUEST_SIGNATURE"] = ""

    unsigned = render_to_string("saml/sp/xml/authn_request.xml", params)
    LOGGER.debug("AuthN Request", unsigned=unsigned)
    if not signed:
        return unsigned

    # Sign it.
    signature_xml = get_signature_xml()
    params["AUTHN_REQUEST_SIGNATURE"] = signature_xml
    signed = render_to_string("saml/sp/xml/authn_request.xml", params)

    LOGGER.debug("AuthN Request", signed=signed)
    return signed
