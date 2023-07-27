from enum import UNIQUE, Enum, verify


@verify(UNIQUE)
class EncryptionType(Enum):
    """
    Kerberos encryption types as defined by IANA.

    See https://www.iana.org/assignments/kerberos-parameters/kerberos-parameters.xhtml#kerberos-parameters-1
    """

    # 0: reserved
    DES_CBC_CRC = 1
    DES_CBC_MD4 = 2
    DES_CBC_MD5 = 3
    DES_CBC_RAW = 4
    DES3_CBC_MD5 = 5
    DES3_CBC_SHA1 = 7
    DES_HMAC_SHA1 = 8
    DSAWITHSHA1_CMSOID = 9
    MD5WITHRSAENCRYPTION_CMSOID = 10
    SHA1WITHRSAENCRYPTION_CMSOID = 11
    RC2CBC_ENVOID = 12
    RSAENCRYPTION_ENVOID = 13
    RSAES_OAEP_ENV_OID = 14
    DES_EDE3_CBC_ENV_OID = 15
    DES3_CBC_SHA1_KD = 16
    AES128_CTS_HMAC_SHA1_96 = 17
    AES256_CTS_HMAC_SHA1_96 = 18
    AES128_CTS_HMAC_SHA256_128 = 19
    AES256_CTS_HMAC_SHA384_192 = 20
    # 21-22: Unassigned
    RC4_HMAC = 23
    RC4_HMAC_EXP = 24
    CAMELLIA128_CTS_CMAC = 25
    CAMELLIA256_CTS_CMAC = 26
    # 27-64: Unassigned
    SUBKEY_KEYMATERIAL = 65
    # 66-2147483647: Unassigned


@verify(UNIQUE)
class ChecksumType(Enum):
    """
    Kerberos checksum types, as defined by IANA, and some others.

    See https://www.iana.org/assignments/kerberos-parameters/kerberos-parameters.xhtml#kerberos-parameters-2
    """

    # 0: Reserved
    CRC32 = 1
    RSA_MD4 = 2
    RSA_MD4_DES = 3
    DES_MAC = 4
    DES_MAC_K = 5
    RSA_MD4_DES_K = 6
    RSA_MD5 = 7
    RSA_MD5_DES = 8
    RSA_MD5_DES3 = 9
    SHA1_10 = 10
    # 11: Unassigned
    HMAC_SHA1_DES3_KD = 12
    HMAC_SHA1_DES3 = 13
    SHA1_14 = 14
    HMAC_SHA1_96_AES128 = 15
    HMAC_SHA1_96_AES256 = 16
    CMAC_CAMELLIA128 = 17
    CMAC_CAMELLIA256 = 18
    HMAC_SHA256_128_AES128 = 19
    HMAC_SHA384_192_AES256 = 20
    # 21-32770: Unassigned
    GSSAPI = 32771
    # 32772-2147483647: Unassigned
    MD5_HMAC_ARCFOUR = -137  # Microsoft netlogon
    HMAC_MD5_ARCFOUR = -138  # RFC 4757


class PreAuthenticationType(Enum):
    """
    Kerberos pre-authentication and Typed data, as defined by IANA.

    See https://www.iana.org/assignments/kerberos-parameters/kerberos-parameters.xhtml#pre-authentication
    """

    PA_TGS_REQ = 1
    PA_ENC_TIMESTAMP = 2
    PA_PW_SALT = 3
    # 4: reserved
    PA_ENC_UNIX_TIME = 5
    PA_SANDIA_SECUREID = 6
    PA_SESAME = 7
    PA_OSF_DCE = 8
    PA_CYBERSAFE_SECUREID = 9
    PA_AFS3_SALT = 10
    PA_ETYPE_INFO = 11
    PA_SAM_CHALLENGE = 12
    PA_SAM_RESPONSE = 13
    PA_PK_AS_REQ_OLD = 14
    PA_PK_AS_REP_OLD = 15
    PA_PK_AS_REQ = 16
    PA_PK_AS_REP = 17
    PA_PK_OCSP_RESPONSE = 18
    PA_ETYPE_INFO2 = 19
    PA_USE_SPECIFIED_KVNO = 20
    PA_SVR_REFERRAL_INFO = 20
    PA_SAM_REDIRECT = 21
    PA_GET_FROM_TYPED_DATA = 22
    TD_PADATA = 22
    PA_SAM_ETYPE_INFO = 23
    PA_ALT_PRINC = 24
    PA_SERVER_REFERRAL = 25
    # 26-29: Unassigned
    PA_SAM_CHALLENGE2 = 30
    PA_SAM_RESPONSE2 = 31
    # 32-40: Unassigned
    PA_EXTRA_TGT = 41
    # 42-100: Unassigned
    TD_PKINIT_CMS_CERTIFICATES = 101
    TD_KRB_PRINCIPAL = 102
    TD_KRB_REALM = 103
    TD_TRUSTED_CERTIFIERS = 104
    TD_CERTIFICATE_INDEX = 105
    TD_APP_DEFINED_ERROR = 106
    TD_REQ_NONCE = 107
    TD_REQ_SEQ = 108
    TD_DH_PARAMETERS = 109
    # 110: Unassigned
    TD_CMS_DIGEST_ALGORITHMS = 111
    TD_CERT_DIGEST_ALGORITHMS = 112
    # 113-127: Unassigned
    PA_PAC_REQUEST = 128
    PA_FOR_USER = 129
    PA_FOR_X509_USER = 130
    PA_FOR_CHECK_DUPS = 131
    PA_AS_CHECKSUM = 132
    PA_FX_COOKIE = 133
    PA_AUTHENTICATION_SET = 134
    PA_AUTH_SET_SELECTED = 135
    PA_FX_FAST = 136
    PA_FX_ERROR = 137
    PA_ENCRYPTED_CHALLENGE = 138
    # 139-140: Unassigned
    PA_OTP_CHALLENGE = 141
    PA_OTP_REQUEST = 142
    PA_OTP_CONFIRM = 143
    PA_OTP_PIN_CHANGE = 144
    PA_EPAK_AS_REQ = 145
    PA_EPAK_AS_REP = 146
    PA_PKINIT_KX = 147
    PA_PKU2U_NAME = 148
    PA_REQ_ENC_PA_REP = 149
    PA_AS_FRESHNESS = 150
    PA_SPAKE = 151
    PA_REDHAT_IDP_OAUTH2 = 152
    PA_REDHAT_PASSKEY = 153
    # 154-164: Unassigned
    PA_SUPPORTED_ETYPES = 165
    PA_EXTENDED_ERROR = 166
