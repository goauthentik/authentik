"""ID/Secret Generators"""
import string
from random import SystemRandom


def generate_id(length=40):
    """Generate a random client ID"""
    rand = SystemRandom()
    return "".join(rand.choice(string.ascii_letters + string.digits) for x in range(length))


def generate_key(length=128):
    """Generate a suitable client secret"""
    rand = SystemRandom()
    return "".join(
        rand.choice(string.ascii_letters + string.digits + string.punctuation)
        for x in range(length)
    )
