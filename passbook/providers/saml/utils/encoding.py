"""Wrappers to de/encode and de/inflate strings"""
import base64
import zlib


def decode_base64_and_inflate(b64string):
    """Base64 decode and ZLib decompress b64string"""
    decoded_data = base64.b64decode(b64string)
    try:
        return zlib.decompress(decoded_data, -15)
    except zlib.error:
        return decoded_data


def deflate_and_base64_encode(string_val):
    """Base64 and ZLib Compress b64string"""
    zlibbed_str = zlib.compress(string_val)
    compressed_string = zlibbed_str[2:-4]
    return base64.b64encode(compressed_string)


def nice64(src):
    """ Returns src base64-encoded and formatted nicely for our XML. """
    return base64.b64encode(src).decode("utf-8").replace("\n", "")
