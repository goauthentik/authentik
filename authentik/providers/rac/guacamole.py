"""Helpers for filtering Guacamole WebSocket tunnel instructions."""

from typing import Never, TypeVar, cast

INSTRUCTION_MAX_LENGTH = 8192
INSTRUCTION_MAX_DIGITS = 5
INSTRUCTION_MAX_ELEMENTS = 64
PING_ELEMENT_COUNT = 3
MAX_BMP_CODEPOINT = 0xFFFF

GuacamoleData = str | bytes
GuacamoleResponses = list[str] | list[bytes]
GuacamoleDataType = TypeVar("GuacamoleDataType", str, bytes)


def _wire_length(data: GuacamoleData) -> int:
    """Return the length used by Guacamole for a text or binary payload."""
    if isinstance(data, bytes):
        return len(data)
    return sum(2 if ord(character) > MAX_BMP_CODEPOINT else 1 for character in data)


class GuacamoleProtocolError(ValueError):
    """Raised when Guacamole protocol data is malformed."""


class GuacamoleInstructionParser:
    """Incrementally parse and filter Guacamole tunnel instructions."""

    def __init__(self):
        self._buffer: GuacamoleData = ""

    def receive(self, data: GuacamoleData) -> tuple[GuacamoleResponses, GuacamoleData]:
        """Return tunnel ping responses and non-internal data to forward."""
        if isinstance(data, str):
            if isinstance(self._buffer, bytes) and self._buffer:
                self._fail("Cannot mix text and binary Guacamole data")
            buffer = (self._buffer if isinstance(self._buffer, str) else "") + data
            responses, forwarded, self._buffer = self._parse(buffer, ".", ",", ";")
        else:
            if isinstance(self._buffer, str) and self._buffer:
                self._fail("Cannot mix text and binary Guacamole data")
            buffer = (self._buffer if isinstance(self._buffer, bytes) else b"") + data
            responses, forwarded, self._buffer = self._parse(buffer, b".", b",", b";")
        return responses, forwarded

    def _parse(
        self,
        buffer: GuacamoleDataType,
        period: GuacamoleDataType,
        comma: GuacamoleDataType,
        semicolon: GuacamoleDataType,
    ) -> tuple[list[GuacamoleDataType], GuacamoleDataType, GuacamoleDataType]:
        responses: list[GuacamoleDataType] = []
        forwarded: list[GuacamoleDataType] = []
        elements: list[GuacamoleDataType] = []
        instruction_start = 0
        position = 0

        while position < len(buffer):
            length_end = buffer.find(period, position)
            if length_end == -1:
                prefix = buffer[position:]
                if len(prefix) > INSTRUCTION_MAX_DIGITS or not self._is_digits(prefix):
                    self._fail("Invalid Guacamole element length")
                break

            prefix = buffer[position:length_end]
            if not prefix or len(prefix) > INSTRUCTION_MAX_DIGITS or not self._is_digits(prefix):
                self._fail("Invalid Guacamole element length")

            element_length = int(prefix)
            if element_length > INSTRUCTION_MAX_LENGTH:
                self._fail("Guacamole element exceeds maximum length")
            content_start = length_end + 1
            content_end = self._content_end(buffer, content_start, element_length)
            if content_end is None or content_end >= len(buffer):
                break

            terminator = buffer[content_end : content_end + 1]
            if terminator not in (comma, semicolon):
                self._fail("Invalid Guacamole element terminator")

            elements.append(buffer[content_start:content_end])
            if len(elements) > INSTRUCTION_MAX_ELEMENTS:
                self._fail("Guacamole instruction contains too many elements")

            position = content_end + 1
            if _wire_length(buffer[instruction_start:position]) > INSTRUCTION_MAX_LENGTH:
                self._fail("Guacamole instruction exceeds maximum length")

            if terminator == semicolon:
                instruction = buffer[instruction_start:position]
                if elements[0] in ("", b""):
                    # Guacamole.WebSocketTunnel pings are handled by the tunnel
                    # endpoint and all internal instructions are hidden from guacd.
                    if len(elements) >= PING_ELEMENT_COUNT and elements[1] in (
                        "ping",
                        b"ping",
                    ):
                        responses.append(instruction)
                else:
                    forwarded.append(instruction)
                elements = []
                instruction_start = position

        if _wire_length(buffer[instruction_start:]) > INSTRUCTION_MAX_LENGTH:
            self._fail("Guacamole instruction exceeds maximum length")
        if isinstance(buffer, str):
            forwarded_data = "".join(cast(list[str], forwarded))
        else:
            forwarded_data = b"".join(cast(list[bytes], forwarded))
        return responses, cast(GuacamoleDataType, forwarded_data), buffer[instruction_start:]

    def _content_end(
        self, buffer: GuacamoleDataType, content_start: int, element_length: int
    ) -> int | None:
        if isinstance(buffer, bytes):
            content_end = content_start + element_length
            return content_end if content_end <= len(buffer) else None

        content_end = content_start
        code_units = 0
        while content_end < len(buffer) and code_units < element_length:
            code_units += 2 if ord(buffer[content_end]) > MAX_BMP_CODEPOINT else 1
            content_end += 1
        if code_units > element_length:
            self._fail("Guacamole element length splits a UTF-16 character")
        return content_end if code_units == element_length else None

    @staticmethod
    def _is_digits(value: GuacamoleData) -> bool:
        if isinstance(value, bytes):
            return all(ord("0") <= character <= ord("9") for character in value)
        return value.isascii() and value.isdigit()

    def _fail(self, message: str) -> Never:
        self._buffer = ""
        raise GuacamoleProtocolError(message)
