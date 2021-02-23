"""webauthn utils"""
import base64
import os
from django.http import HttpRequest

CHALLENGE_DEFAULT_BYTE_LEN = 32


def generate_challenge(challenge_len=CHALLENGE_DEFAULT_BYTE_LEN):
    """Generate a challenge of challenge_len bytes, Base64-encoded.
    We use URL-safe base64, but we *don't* strip the padding, so that
    the browser can decode it without too much hassle.
    Note that if we are doing byte comparisons with the challenge in collectedClientData
    later on, that value will not have padding, so we must remove the padding
    before storing the value in the session.
    """
    # If we know Python 3.6 or greater is available, we could replace this with one
    # call to secrets.token_urlsafe
    challenge_bytes = os.urandom(challenge_len)
    challenge_base64 = base64.urlsafe_b64encode(challenge_bytes)
    # Python 2/3 compatibility: b64encode returns bytes only in newer Python versions
    if not isinstance(challenge_base64, str):
        challenge_base64 = challenge_base64.decode("utf-8")
    return challenge_base64

def get_rp_id(request: HttpRequest) -> str:
    """Get hostname from http request, without port"""
    host = request.get_host()
    if ":" in host:
        return host.split(":")[0]
    return host

def get_origin(request: HttpRequest) -> str:
    """Return Origin by building an absolute URL and removing the
    trailing slash"""
    full_url = request.build_absolute_uri("/")
    return full_url[:-1]
