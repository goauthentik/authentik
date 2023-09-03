"""Authenticator utils"""
import random
import string
from binascii import unhexlify
from os import urandom

from django.core.exceptions import ValidationError


def hex_validator(length=0):
    """
    Returns a function to be used as a model validator for a hex-encoded
    CharField. This is useful for secret keys of all kinds::

        def key_validator(value):
            return hex_validator(20)(value)

        key = models.CharField(max_length=40,
            validators=[key_validator], help_text='A hex-encoded 20-byte secret key')

    :param int length: If greater than 0, validation will fail unless the
        decoded value is exactly this number of bytes.

    :rtype: function

    >>> hex_validator()('0123456789abcdef')
    >>> hex_validator(8)(b'0123456789abcdef')
    >>> hex_validator()('phlebotinum')          # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: ['phlebotinum is not valid hex-encoded data.']
    >>> hex_validator(9)('0123456789abcdef')    # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
        ...
    ValidationError: ['0123456789abcdef does not represent exactly 9 bytes.']
    """

    def _validator(value):
        try:
            if isinstance(value, str):
                value = value.encode()

            unhexlify(value)
        except Exception:
            raise ValidationError("{0} is not valid hex-encoded data.".format(value))

        if (length > 0) and (len(value) != length * 2):
            raise ValidationError("{0} does not represent exactly {1} bytes.".format(value, length))

    return _validator


def random_hex(length=20):
    """
    Returns a string of random bytes encoded as hex.

    This uses :func:`os.urandom`, so it should be suitable for generating
    cryptographic keys.

    :param int length: The number of (decoded) bytes to return.

    :returns: A string of hex digits.
    :rtype: str

    """
    return urandom(length).hex()


def random_number_token(length=6):
    """
    Returns a string of random digits encoded as string.

    :param int length: The number of digits to return.

    :returns: A string of decimal digits.
    :rtype: str

    """
    rand = random.SystemRandom()

    if hasattr(rand, "choices"):
        digits = rand.choices(string.digits, k=length)
    else:
        digits = (rand.choice(string.digits) for i in range(length))

    return "".join(digits)
