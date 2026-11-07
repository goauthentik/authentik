"""Password hashers"""

from django.contrib.auth.hashers import BCryptPasswordHasher as DjangoBCryptPasswordHasher

BCRYPT_MAX_PASSWORD_BYTES = 72


class BCryptPasswordHasher(DjangoBCryptPasswordHasher):
    """Verify plain bcrypt hashes imported from other applications.

    bcrypt only uses the first 72 bytes of a password. Most implementations (e.g. Ruby's
    bcrypt as used by Devise) silently truncate longer passwords, while the Python bcrypt
    library raises a `ValueError` since version 5. Truncate the encoded password the same
    way, so such hashes still verify and long passwords don't raise during login."""

    def encode(self, password: str, salt: bytes) -> str:
        bcrypt = self._load_library()
        data = bcrypt.hashpw(password.encode()[:BCRYPT_MAX_PASSWORD_BYTES], salt)
        return f"{self.algorithm}${data.decode("ascii")}"
