"""Wrappers to de/encode and de/inflate strings"""
import base64
import zlib


def decode_base64_and_inflate(encoded: str, encoding="utf-8") -> str:
    """Base64 decode and ZLib decompress b64string"""
    decoded_data = base64.b64decode(encoded)
    try:
        return zlib.decompress(decoded_data, -15).decode(encoding)
    except zlib.error:
        return decoded_data.decode(encoding)


def deflate_and_base64_encode(inflated: str, encoding="utf-8"):
    """Base64 and ZLib Compress b64string"""
    zlibbed_str = zlib.compress(inflated.encode())
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string).decode(encoding)


def nice64(src):
    """Returns src base64-encoded and formatted nicely for our XML. """
    return base64.b64encode(src).decode("utf-8").replace("\n", "")
