"""Guacamole framing for display and bounded RAC control messages.

Lengths count Unicode code points, not UTF-8 bytes. Instructions may span
WebSocket messages; delimiters within length-prefixed elements are data.
"""

from codecs import getincrementaldecoder
from collections.abc import Iterator
from unicodedata import category

from authentik.providers.rac.guacamole import GuacamoleInstructionParser

MAX_INSTRUCTION = 16 * 1024 * 1024
UTF16_MAX = 0xFFFF
MAX_FILE_PATH = 4096
CONTROL_TIMEOUT = 10
CONTROL_MAX_REQUESTS = 8


def instruction(*elements: object, utf16: bool = False) -> str:
    """Encode a Guacamole instruction without interpreting its contents."""

    def element(value: object) -> str:
        text = str(value)
        length = len(text.encode("utf-16-le")) // 2 if utf16 else len(text)
        return f"{length}.{text}"

    return ",".join(element(value) for value in elements) + ";"


def valid_file_path(value: str) -> bool:
    """Accept canonical absolute paths within the redirected RDP drive only."""
    return (
        value.startswith("/")
        and not any(category(char) in {"Cc", "Cs"} for char in value)
        and len(value.encode("utf-8")) <= MAX_FILE_PATH
        and "\\" not in value
        and (value == "/" or all(part not in {"", ".", ".."} for part in value[1:].split("/")))
    )


class InstructionParser:
    """Adapt guacd text/UTF-8 frames to the shared Guacamole instruction parser.

    Browser parsing retains the upstream defaults. The trusted Outpost stream
    uses Unicode code points and a larger, bounded limit for display payloads.
    """

    def __init__(self, utf16: bool = False) -> None:
        self.decoder = getincrementaldecoder("utf-8")()
        self.parser = GuacamoleInstructionParser(
            utf16=utf16, max_instruction_length=MAX_INSTRUCTION, max_elements=None
        )

    def feed(self, data: str | bytes) -> Iterator[list[str]]:
        """Decode split UTF-8 frames and expose parsed elements to the bridge."""
        text = self.decoder.decode(data) if isinstance(data, bytes) else data
        for _, elements in self.parser.feed(text):
            yield elements
