"""Authenticator utils"""

import random
import string
from binascii import Error, unhexlify
from os import urandom

from django.core.exceptions import ValidationError


def hex_validator(length=0):
    """Validator for hex-encoded values, optionally of exactly `length` bytes

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
        except Error:
            raise ValidationError(f"{value} is not valid hex-encoded data.") from None

        if (length > 0) and (len(value) != length * 2):
            raise ValidationError(f"{value} does not represent exactly {length} bytes.")

    return _validator


def random_hex(length=20):
    """Random hex string of `length` bytes, suitable for cryptographic keys"""
    return urandom(length).hex()


def random_number_token(length=6):
    """Random numeric token of `length` digits"""
    rand = random.SystemRandom()

    if hasattr(rand, "choices"):
        digits = rand.choices(string.digits, k=length)
    else:
        digits = (rand.choice(string.digits) for i in range(length))

    return "".join(digits)
