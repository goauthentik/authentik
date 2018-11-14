"""URL-related utils"""
from urllib.parse import urlparse


def is_url_absolute(url):
    """Check if domain is absolute to prevent user from being redirect somewhere else"""
    return bool(urlparse(url).netloc)
