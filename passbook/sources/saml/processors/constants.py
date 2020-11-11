"""SAML Source processor constants"""
NS_SAML_PROTOCOL = "urn:oasis:names:tc:SAML:2.0:protocol"
NS_SAML_ASSERTION = "urn:oasis:names:tc:SAML:2.0:assertion"
NS_SAML_METADATA = "urn:oasis:names:tc:SAML:2.0:metadata"
NS_SIGNATURE = "http://www.w3.org/2000/09/xmldsig#"

NS_MAP = {
    "samlp": NS_SAML_PROTOCOL,
    "saml": NS_SAML_ASSERTION,
    "ds": NS_SIGNATURE,
    "md": NS_SAML_METADATA,
}

SAML_NAME_ID_FORMAT_EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
SAML_NAME_ID_FORMAT_PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
SAML_NAME_ID_FORMAT_X509 = "urn:oasis:names:tc:SAML:2.0:nameid-format:X509SubjectName"
SAML_NAME_ID_FORMAT_WINDOWS = (
    "urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName"
)
SAML_NAME_ID_FORMAT_TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"

SAML_BINDING_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
SAML_BINDING_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"

DSA_SHA1 = 'http://www.w3.org/2000/09/xmldsig#dsa-sha1'
RSA_SHA1 = 'http://www.w3.org/2000/09/xmldsig#rsa-sha1'
RSA_SHA256 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256'
RSA_SHA384 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha384'
RSA_SHA512 = 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha512'
