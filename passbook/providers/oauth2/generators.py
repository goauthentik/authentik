"""OAuth2 Client ID/Secret Generators"""
import string
from random import SystemRandom


def generate_client_id():
    """Generate a random client ID"""
    rand = SystemRandom()
    return "".join(rand.choice(string.ascii_letters + string.digits) for x in range(40))


def generate_client_secret():
    """Generate a suitable client secret"""
    rand = SystemRandom()
    return "".join(
        rand.choice(string.ascii_letters + string.digits) for x in range(128)
    )
