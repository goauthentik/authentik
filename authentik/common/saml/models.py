"""SAML choice sets shared between providers and sources"""

from django.db import models

from authentik.common.saml import constants
from authentik.lib.models import GeneratedEnum


class DigestAlgorithm(GeneratedEnum):
    """XML digest algorithms"""

    SHA1 = constants.SHA1, "SHA1"
    SHA256 = constants.SHA256, "SHA256"
    SHA384 = constants.SHA384, "SHA384"
    SHA512 = constants.SHA512, "SHA512"


class SignatureAlgorithm(models.TextChoices):
    """XML signature algorithms"""

    RSA_SHA1 = constants.RSA_SHA1, "RSA-SHA1"
    RSA_SHA256 = constants.RSA_SHA256, "RSA-SHA256"
    RSA_SHA384 = constants.RSA_SHA384, "RSA-SHA384"
    RSA_SHA512 = constants.RSA_SHA512, "RSA-SHA512"
    ECDSA_SHA1 = constants.ECDSA_SHA1, "ECDSA-SHA1"
    ECDSA_SHA256 = constants.ECDSA_SHA256, "ECDSA-SHA256"
    ECDSA_SHA384 = constants.ECDSA_SHA384, "ECDSA-SHA384"
    ECDSA_SHA512 = constants.ECDSA_SHA512, "ECDSA-SHA512"
    DSA_SHA1 = constants.DSA_SHA1, "DSA-SHA1"
