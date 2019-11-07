#XXX: Use svn:externals to get the same version as in saml2idp???
"""
Signing code goes here.
"""
# # python:
# import hashlib
# import string

from structlog import get_logger

# other libraries:
# this app:
# from passbook.providers.saml.utils import nice64
# from passbook.sources.saml.xml_templates import SIGNATURE, SIGNED_INFO

LOGGER = get_logger()

# def get_signature_xml(subject, reference_uri):
#     """
#     Returns XML Signature for subject.
#     """
#     private_key_file = saml2sp_settings.SAML2SP_PRIVATE_KEY_FILE
#     certificate_file = saml2sp_settings.SAML2SP_CERTIFICATE_FILE
#     LOGGER.debug('get_signature_xml - Begin.')
#     LOGGER.debug('Using private key file: ' + private_key_file)
#     LOGGER.debug('Using certificate file: ' + certificate_file)
#     LOGGER.debug('Subject: ' + subject)

#     # Hash the subject.
#     subject_hash = hashlib.sha1()
#     subject_hash.update(subject)
#     subject_digest = nice64(subject_hash.digest())
#     LOGGER.debug('Subject digest: ' + subject_digest)

#     # Create signed_info.
#     signed_info = string.Template(SIGNED_INFO).substitute({
#         'REFERENCE_URI': reference_uri,
#         'SUBJECT_DIGEST': subject_digest,
#     })
#     LOGGER.debug('SignedInfo XML: ' + signed_info)

# #    # "Digest" the signed_info.
# #    info_hash = hashlib.sha1()
# #    info_hash.update(signed_info)
# #    info_digest = info_hash.digest()
# #    LOGGER.debug('Info digest: ' + nice64(info_digest))

#     # RSA-sign the signed_info.
#     private_key = M2Crypto.EVP.load_key(private_key_file)
#     private_key.sign_init()
#     private_key.sign_update(signed_info)
#     rsa_signature = nice64(private_key.sign_final())
#     LOGGER.debug('RSA Signature: ' + rsa_signature)

#     # Load the certificate.
#     cert_data = load_cert_data(certificate_file)

#     # Put the signed_info and rsa_signature into the XML signature.
#     signed_info_short = signed_info.replace('xmlns:ds="http://www.w3.org/2000/09/xmldsig#"', '')
#     signature_xml = string.Template(SIGNATURE).substitute({
#         'RSA_SIGNATURE': rsa_signature,
#         'SIGNED_INFO': signed_info_short,
#         'CERTIFICATE': cert_data,
#     })
#     LOGGER.debug('Signature XML: ' + signature_xml)
#     return signature_xml
