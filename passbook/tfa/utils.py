"""passbook Mod 2FA Utils"""

from django.conf import settings
from django.utils.http import urlencode


def otpauth_url(accountname, secret, issuer=None, digits=6):
    """Create otpauth according to
    https://github.com/google/google-authenticator/wiki/Key-Uri-Format"""

    accountname = accountname
    issuer = issuer if issuer else getattr(settings, 'OTP_TOTP_ISSUER')

    # Ensure that the secret parameter is the FIRST parameter of the URI, this
    # allows Microsoft Authenticator to work.
    query = [
        ('secret', secret),
        ('digits', digits),
        ('issuer', issuer),
    ]

    return 'otpauth://totp/%s:%s?%s' % (issuer, accountname, urlencode(query))
