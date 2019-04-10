"""Exception classes"""

class ReverseProxyException(Exception):
    """Base for revproxy exception"""


class InvalidUpstream(ReverseProxyException):
    """Invalid upstream set"""
