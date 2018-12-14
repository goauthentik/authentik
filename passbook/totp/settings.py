"""passbook TOTP Settings"""

OTP_LOGIN_URL = 'passbook_tfa:tfa-verify'
OTP_TOTP_ISSUER = 'passbook'
MIDDLEWARE = [
    'django_otp.middleware.OTPMiddleware',
    'passbook.tfa.middleware.tfa_force_verify',
]
INSTALLED_APPS = [
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
]
