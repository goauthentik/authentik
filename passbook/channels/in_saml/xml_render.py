"""Functions for creating XML output."""
from structlog import get_logger

from passbook.channels.out_saml.utils.xml_signing import get_signature_xml
from passbook.lib.utils.template import render_to_string

LOGGER = get_logger()


def get_authnrequest_xml(parameters, signed=False):
    """Get AuthN Request XML"""
    # Reset signature.
    params = {}
    params.update(parameters)
    params["AUTHN_REQUEST_SIGNATURE"] = ""

    unsigned = render_to_string("saml/sp/xml/authn_request.xml", params)
    if not signed:
        return unsigned

    # Sign it.
    signature_xml = get_signature_xml()
    params["AUTHN_REQUEST_SIGNATURE"] = signature_xml
    signed = render_to_string("saml/sp/xml/authn_request.xml", params)

    return signed
