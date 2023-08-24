"""AWS Helpers"""
import base64
import hashlib
import hmac

# These values are required to calculate the signature. Do not change them.
AWS_DATE = "11111111"
AWS_SERVICE = "ses"
AWS_MESSAGE = "SendRawEmail"
AWS_TERMINAL = "aws4_request"
AWS_VERSION = 0x04


# https://docs.aws.amazon.com/ses/latest/dg/smtp-credentials.html#smtp-credentials-convert


def aws_sign(key: bytes, msg: bytes) -> bytes:
    """Hmac sign"""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def aws_calculate_password(secret_access_key: str, region: str) -> str:
    """Calculate AWS SMTP password from secret key"""
    signature = aws_sign(("AWS4" + secret_access_key).encode("utf-8"), AWS_DATE)
    signature = aws_sign(signature, region)
    signature = aws_sign(signature, AWS_SERVICE)
    signature = aws_sign(signature, AWS_TERMINAL)
    signature = aws_sign(signature, AWS_MESSAGE)
    signature_and_version = bytes([AWS_VERSION]) + signature
    smtp_password = base64.b64encode(signature_and_version)
    return smtp_password.decode("utf-8")
