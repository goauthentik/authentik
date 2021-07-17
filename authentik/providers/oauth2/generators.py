"""OAuth2 Client ID/Secret Generators"""
from random import SystemRandom
from string import ascii_letters, digits, punctuation

ID_CHARS = digits + ascii_letters
TOKEN_CHARS = digits + ascii_letters + punctuation


def generate_client_id():
    """Generate a random client ID"""
    rand = SystemRandom()
    return "".join(rand.choice(ID_CHARS) for x in range(40))


def generate_client_secret():
    """Generate a suitable client secret"""
    rand = SystemRandom()
    return "".join(
        rand.choice(TOKEN_CHARS) for x in range(128)
    )
