"""XML Utilities"""

from lxml.etree import XMLParser, _Element, fromstring, tostring  # nosec


def get_lxml_parser():
    """Get XML parser"""
    return XMLParser(resolve_entities=False)


def lxml_from_string(text: str):
    """Wrapper around fromstring"""
    return fromstring(text, parser=get_lxml_parser())  # nosec


def remove_xml_newlines(parent: _Element, element: _Element):
    """Remove newlines in a given XML element, required for xmlsec

    https://github.com/xmlsec/python-xmlsec/issues/196"""
    old_element = element
    new_node = fromstring(tostring(element, encoding=str).replace('\n',''))
    parent.replace(old_element, new_node)
    return new_node
