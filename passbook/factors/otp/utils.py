"""passbook OTP Utils"""

from django.utils.http import urlencode


def otpauth_url(accountname, secret, issuer=None, digits=6):
    """Create otpauth according to
    https://github.com/google/google-authenticator/wiki/Key-Uri-Format"""
    # Ensure that the secret parameter is the FIRST parameter of the URI, this
    # allows Microsoft Authenticator to work.
    query = [
        ('secret', secret),
        ('digits', digits),
        ('issuer', 'passbook'),
    ]

    return 'otpauth://totp/%s:%s?%s' % (issuer, accountname, urlencode(query))
