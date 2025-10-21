"""ID/Secret Generators"""

import string
from random import SystemRandom


def generate_code_fixed_length(length=9) -> str:
    """Generate a numeric code"""
    rand = SystemRandom()
    num = rand.randrange(1, 10**length)
    return str(num).zfill(length)


def generate_id(length=40) -> str:
    """Generate a random client ID"""
    rand = SystemRandom()
    return "".join(rand.choice(string.ascii_letters + string.digits) for x in range(length))


def generate_key(length=128) -> str:
    """Generate a suitable client secret"""
    rand = SystemRandom()
    return "".join(
        rand.choice(string.ascii_letters + string.digits + string.punctuation)
        for x in range(length)
    )
