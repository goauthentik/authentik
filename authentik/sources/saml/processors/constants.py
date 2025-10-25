"""SAML Source processor constants"""

import xmlsec

NS_SAML_PROTOCOL = "urn:oasis:names:tc:SAML:2.0:protocol"
NS_SAML_ASSERTION = "urn:oasis:names:tc:SAML:2.0:assertion"
NS_SAML_METADATA = "urn:oasis:names:tc:SAML:2.0:metadata"
NS_SIGNATURE = "http://www.w3.org/2000/09/xmldsig#"
NS_ENC = "http://www.w3.org/2001/04/xmlenc#"

NS_MAP = {
    "samlp": NS_SAML_PROTOCOL,
    "saml": NS_SAML_ASSERTION,
    "ds": NS_SIGNATURE,
    "md": NS_SAML_METADATA,
    "xenc": NS_ENC,
}

SAML_NAME_ID_FORMAT_EMAIL = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
SAML_NAME_ID_FORMAT_PERSISTENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
SAML_NAME_ID_FORMAT_UNSPECIFIED = "urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified"
SAML_NAME_ID_FORMAT_X509 = "urn:oasis:names:tc:SAML:1.1:nameid-format:X509SubjectName"
SAML_NAME_ID_FORMAT_WINDOWS = "urn:oasis:names:tc:SAML:2.0:nameid-format:WindowsDomainQualifiedName"
SAML_NAME_ID_FORMAT_TRANSIENT = "urn:oasis:names:tc:SAML:2.0:nameid-format:transient"

SAML_ATTRIBUTES_GROUP = "http://schemas.xmlsoap.org/claims/Group"

SAML_BINDING_POST = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
SAML_BINDING_REDIRECT = "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"

DSA_SHA1 = "http://www.w3.org/2000/09/xmldsig#dsa-sha1"
RSA_SHA1 = "http://www.w3.org/2000/09/xmldsig#rsa-sha1"
# https://datatracker.ietf.org/doc/html/rfc4051#section-2.3.2
RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
RSA_SHA384 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha384"
RSA_SHA512 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha512"
# https://datatracker.ietf.org/doc/html/rfc4051#section-2.3.6
ECDSA_SHA1 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha1"
ECDSA_SHA224 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha224"
ECDSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256"
ECDSA_SHA384 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha384"
ECDSA_SHA512 = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512"

SHA1 = "http://www.w3.org/2000/09/xmldsig#sha1"
SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
SHA384 = "http://www.w3.org/2001/04/xmldsig-more#sha384"
SHA512 = "http://www.w3.org/2001/04/xmlenc#sha512"

SIGN_ALGORITHM_TRANSFORM_MAP = {
    DSA_SHA1: xmlsec.constants.TransformDsaSha1,
    RSA_SHA1: xmlsec.constants.TransformRsaSha1,
    RSA_SHA256: xmlsec.constants.TransformRsaSha256,
    RSA_SHA384: xmlsec.constants.TransformRsaSha384,
    RSA_SHA512: xmlsec.constants.TransformRsaSha512,
    ECDSA_SHA1: xmlsec.constants.TransformEcdsaSha1,
    ECDSA_SHA224: xmlsec.constants.TransformEcdsaSha224,
    ECDSA_SHA256: xmlsec.constants.TransformEcdsaSha256,
    ECDSA_SHA384: xmlsec.constants.TransformEcdsaSha384,
    ECDSA_SHA512: xmlsec.constants.TransformEcdsaSha512,
}

DIGEST_ALGORITHM_TRANSLATION_MAP = {
    SHA1: xmlsec.constants.TransformSha1,
    SHA256: xmlsec.constants.TransformSha256,
    SHA384: xmlsec.constants.TransformSha384,
    SHA512: xmlsec.constants.TransformSha512,
}
