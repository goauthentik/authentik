"""XML Utilities"""

from lxml.etree import XMLParser, _Element, fromstring  # nosec


def get_lxml_parser() -> XMLParser:
    """Get XML parser"""
    return XMLParser(resolve_entities=False)


def lxml_from_string(text: str) -> _Element:
    """Wrapper around fromstring"""
    return fromstring(text, parser=get_lxml_parser())  # nosec
