"""passbook TOTP Settings"""

OTP_LOGIN_URL = 'passbook_totp:totp-verify'
OTP_TOTP_ISSUER = 'passbook'
MIDDLEWARE = [
    'django_otp.middleware.OTPMiddleware',
    'passbook.totp.middleware.totp_force_verify',
]
INSTALLED_APPS = [
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
]
