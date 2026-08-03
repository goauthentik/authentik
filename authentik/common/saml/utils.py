"""Shared SAML XML helpers"""

from collections.abc import Iterator
from typing import cast

from lxml.etree import _Element


def get_element_text(element: _Element) -> str:
    """Return the full text content of an XML element.

    ``Element.text`` only returns the text up to the first child node, so a value
    containing an XML comment (for example ``admin<!--x-->_user``) is silently
    truncated to ``admin``. Comment-excluding signature canonicalization
    (``xml-exc-c14n``) strips those comments before the digest is computed, so a
    signed value can be truncated after signing while keeping the signature valid.
    Reading the text via ``itertext()`` keeps the value equal to what was signed.
    """
    return "".join(cast(Iterator[str], element.itertext()))
