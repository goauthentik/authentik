"""XML Utilities"""

from typing import NoReturn
from xml.parsers import expat  # nosec

from lxml.etree import XMLParser, _Element, fromstring, tostring  # nosec


class UnsafeXML(ValueError):
    """A document uses XML features that are not accepted."""


class _RootElement(Exception):
    """The scan reached the root element. expat offers no other way to stop it."""


class _Doctype(Exception):
    """The scan reached a document type declaration."""


def _reject_doctype(data: bytes) -> None:
    """Refuse a document type declaration.

    The check runs on expat rather than on the parser below, and looks for a
    declaration rather than for its text, because a document may be in any encoding.
    Parsing stops at the root element, so only the prolog is read."""
    parser = expat.ParserCreate()

    def start_doctype(
        name: str, system_id: str | None, public_id: str | None, has_internal_subset: int
    ) -> NoReturn:
        raise _Doctype

    def start_element(name: str, attributes: dict[str, str]) -> NoReturn:
        raise _RootElement

    parser.StartDoctypeDeclHandler = start_doctype
    parser.StartElementHandler = start_element
    try:
        parser.Parse(data, True)
    except _RootElement:
        pass
    except _Doctype:
        raise UnsafeXML("XML document contains a DOCTYPE declaration") from None
    except (expat.ExpatError, LookupError, ValueError) as exc:
        # An encoding this parser cannot read is reported as any of these three. A
        # document that cannot be read here is not one to hand to the parser below.
        raise UnsafeXML("XML document could not be validated") from exc


def get_lxml_parser():
    """Get XML parser"""
    return XMLParser(resolve_entities=False)


def lxml_from_string(text: str | bytes) -> _Element:
    """Wrapper around fromstring"""
    data = text.encode() if isinstance(text, str) else text
    _reject_doctype(data)
    return fromstring(data, parser=get_lxml_parser())  # nosec


def remove_xml_newlines(parent: _Element, element: _Element):
    """Remove newlines in a given XML element, required for xmlsec

    https://github.com/xmlsec/python-xmlsec/issues/196"""
    old_element = element
    new_node = fromstring(tostring(element, encoding=str).replace("\n", ""))
    parent.replace(old_element, new_node)
    return new_node
