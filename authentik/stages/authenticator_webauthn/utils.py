import base64
import os

CHALLENGE_DEFAULT_BYTE_LEN = 32
UKEY_DEFAULT_BYTE_LEN = 20
USERNAME_MAX_LENGTH = 32
DISPLAY_NAME_MAX_LENGTH = 65


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


def generate_ukey():
    """Its value's id member is required, and contains an identifier
    for the account, specified by the Relying Party. This is not meant
    to be displayed to the user, but is used by the Relying Party to
    control the number of credentials - an authenticator will never
    contain more than one credential for a given Relying Party under
    the same id.
    A unique identifier for the entity. For a relying party entity,
    sets the RP ID. For a user account entity, this will be an
    arbitrary string specified by the relying party.
    """
    return generate_challenge(UKEY_DEFAULT_BYTE_LEN)
