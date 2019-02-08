"""passbook captcha_facot settings"""
RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
NOCAPTCHA = True
INSTALLED_APPS = [
    'captcha'
]
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']
