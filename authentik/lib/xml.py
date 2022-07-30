"""XML Utilities"""
from lxml.etree import XMLParser, fromstring  # nosec


def get_lxml_parser():
    """Get XML parser"""
    return XMLParser(resolve_entities=False)


def lxml_from_string(text: str):
    """Wrapper around fromstring"""
    return fromstring(text, parser=get_lxml_parser())
