"""Wrappers to de/encode and de/inflate strings"""

import base64
import zlib
from ssl import PEM_FOOTER, PEM_HEADER

from structlog.stdlib import get_logger

from authentik.providers.saml.exceptions import CannotHandleAssertion

LOGGER = get_logger()
MAX_INFLATED_SIZE_BYTES = 1 * 1024 * 1024


def decode_base64_and_inflate(encoded: str, encoding="utf-8") -> str:
    """Base64 decode and ZLib decompress b64string"""
    decoded_data = base64.b64decode(encoded)
    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)  # raw deflate
    try:
        inflated = decompressor.decompress(decoded_data, MAX_INFLATED_SIZE_BYTES + 1)
    except zlib.error:
        return decoded_data.decode(encoding)
    if len(inflated) > MAX_INFLATED_SIZE_BYTES:
        raise CannotHandleAssertion(
            f"Inflated SAML message exceeds {MAX_INFLATED_SIZE_BYTES} bytes"
        )
    if not decompressor.eof:
        LOGGER.warning("Incomplete deflate stream in SAML message")
        return decoded_data.decode(encoding)
    return inflated.decode(encoding)


def deflate_and_base64_encode(inflated: str, encoding="utf-8"):
    """Base64 and ZLib Compress b64string"""
    zlibbed_str = zlib.compress(inflated.encode())
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).decode(encoding)


def nice64(src: str) -> str:
    """Returns src base64-encoded and formatted nicely for our XML."""
    return base64.b64encode(src.encode()).decode("utf-8").replace("\n", "")


def strip_pem_header(cert: str) -> str:
    """Remove PEM Headers"""
    return cert.replace(PEM_HEADER, "").replace(PEM_FOOTER, "").replace("\n", "")
