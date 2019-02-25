"""passbook OTP Settings"""

OTP_TOTP_ISSUER = 'passbook'
MIDDLEWARE = [
    'django_otp.middleware.OTPMiddleware',
]
INSTALLED_APPS = [
    'django_otp',
    'django_otp.plugins.otp_static',
    'django_otp.plugins.otp_totp',
]
