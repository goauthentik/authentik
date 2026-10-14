"""OATH helpers"""

import hmac
from hashlib import sha1
from struct import pack
from time import time


def hotp(key: bytes, counter: int, digits=6) -> int:
    """HOTP as defined in RFC 4226

    >>> key = b'12345678901234567890'
    >>> for c in range(10):
    ...     hotp(key, c)
    755224
    287082
    359152
    969429
    338314
    254676
    287922
    162583
    399871
    520489
    """
    msg = pack(b">Q", counter)
    hs = hmac.new(key, msg, sha1).digest()
    hs = list(iter(hs))

    offset = hs[19] & 0x0F
    bin_code = (
        (hs[offset] & 0x7F) << 24 | hs[offset + 1] << 16 | hs[offset + 2] << 8 | hs[offset + 3]
    )
    return bin_code % pow(10, digits)


def totp(key: bytes, step=30, t0=0, digits=6, drift=0) -> int:
    """TOTP as defined in RFC 6238. `drift` shifts the time step to account
    for clock differences.

    >>> key = b'12345678901234567890'
    >>> now = int(time())
    >>> for delta in range(0, 200, 20):
    ...     totp(key, t0=(now-delta))
    755224
    755224
    287082
    359152
    359152
    969429
    338314
    338314
    254676
    287922
    """
    return TOTP(key, step, t0, digits, drift).token()


class TOTP:
    """TOTP with access to intermediate steps of the computation. Values of `t()`
    and `token()` change over time unless `time` is set to a fixed value.

    >>> key = b'12345678901234567890'
    >>> totp = TOTP(key)
    >>> totp.time = 0
    >>> totp.t()
    0
    >>> totp.token()
    755224
    >>> totp.time = 30
    >>> totp.t()
    1
    >>> totp.token()
    287082
    >>> totp.verify(287082)
    True
    >>> totp.verify(359152)
    False
    >>> totp.verify(359152, tolerance=1)
    True
    >>> totp.drift
    1
    >>> totp.drift = 0
    >>> totp.verify(359152, tolerance=1, min_t=3)
    False
    >>> totp.drift
    0
    >>> del totp.time
    >>> totp.t0 = int(time()) - 60
    >>> totp.t()
    2
    >>> totp.token()
    359152
    """

    def __init__(self, key: bytes, step=30, t0=0, digits=6, drift=0):
        self.key = key
        self.step = step
        self.t0 = t0
        self.digits = digits
        self.drift = drift
        self._time = None

    def token(self):
        """The computed TOTP token."""
        return hotp(self.key, self.t(), digits=self.digits)

    def t(self):
        """The computed time step."""
        return ((int(self.time) - self.t0) // self.step) + self.drift

    @property
    def time(self):
        """Current time, or the fixed value if set. Delete to return to live time."""
        return self._time if (self._time is not None) else time()

    @time.setter
    def time(self, value):
        self._time = value

    @time.deleter
    def time(self):
        self._time = None

    def verify(self, token, tolerance=0, min_t=None):
        """Verify a token within `tolerance` steps, rejecting steps below `min_t`.
        On success, `drift` is updated to the matching offset."""
        drift_orig = self.drift
        verified = False

        for offset in range(-tolerance, tolerance + 1):
            self.drift = drift_orig + offset
            if (min_t is not None) and (self.t() < min_t):
                continue
            if self.token() == token:
                verified = True
                break
        else:
            self.drift = drift_orig

        return verified
