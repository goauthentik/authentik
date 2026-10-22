"""Helpers for parsing and filtering Guacamole WebSocket tunnel instructions."""

from typing import Never

INSTRUCTION_MAX_LENGTH = 8192
INSTRUCTION_MAX_DIGITS = 5
INSTRUCTION_MAX_ELEMENTS = 64
PING_ELEMENT_COUNT = 3
MAX_BMP_CODEPOINT = 0xFFFF


class GuacamoleProtocolError(ValueError):
    """Raised when Guacamole protocol data is malformed."""


class GuacamoleInstructionParser:
    """Incrementally split a Guacamole stream into complete instructions."""

    def __init__(self):
        self._buffer = ""

    def feed(self, data: str) -> list[tuple[str, list[str]]]:
        """Return the instructions completed by `data`, buffering any partial tail."""
        instructions, self._buffer = self._parse(self._buffer + data)
        return instructions

    def _parse(self, buffer: str) -> tuple[list[tuple[str, list[str]]], str]:
        """Parse guacamole instruction(s) into a list of
        [
            (op code, [*args]),
            [...]
        ]
        """
        instructions: list[tuple[str, list[str]]] = []
        elements: list[str] = []
        instruction_start = 0
        position = 0

        while position < len(buffer):
            length_end = buffer.find(".", position)
            if length_end == -1:
                # Partial length prefix, validate what we have and wait for more.
                self._check_length_prefix(buffer[position:])
                break

            prefix = buffer[position:length_end]
            self._check_length_prefix(prefix)
            element_length = int(prefix)
            if element_length > INSTRUCTION_MAX_LENGTH:
                self._fail("Guacamole element exceeds maximum length")

            content_start = length_end + 1
            content_end = self._content_end(buffer, content_start, element_length)
            if content_end is None or content_end >= len(buffer):
                break

            terminator = buffer[content_end]
            if terminator not in (",", ";"):
                self._fail("Invalid Guacamole element terminator")

            elements.append(buffer[content_start:content_end])
            if len(elements) > INSTRUCTION_MAX_ELEMENTS:
                self._fail("Guacamole instruction contains too many elements")

            position = content_end + 1
            if self._wire_length(buffer[instruction_start:position]) > INSTRUCTION_MAX_LENGTH:
                self._fail("Guacamole instruction exceeds maximum length")

            if terminator == ";":
                instructions.append((buffer[instruction_start:position], elements))
                elements = []
                instruction_start = position

        if self._wire_length(buffer[instruction_start:]) > INSTRUCTION_MAX_LENGTH:
            self._fail("Guacamole instruction exceeds maximum length")
        return instructions, buffer[instruction_start:]

    def _content_end(self, buffer: str, content_start: int, element_length: int) -> int | None:
        """Return the index just past an element of `element_length` UTF-16 code units."""
        content_end = content_start
        code_units = 0
        while content_end < len(buffer) and code_units < element_length:
            code_units += 2 if ord(buffer[content_end]) > MAX_BMP_CODEPOINT else 1
            content_end += 1
        if code_units > element_length:
            self._fail("Guacamole element length splits a UTF-16 character")
        return content_end if code_units == element_length else None

    def _wire_length(self, data: str) -> int:
        """Return the length Guacamole uses for a payload, in UTF-16 code units."""
        return sum(2 if ord(character) > MAX_BMP_CODEPOINT else 1 for character in data)

    def _check_length_prefix(self, prefix: str) -> None:
        if (
            not prefix
            or len(prefix) > INSTRUCTION_MAX_DIGITS
            or not (prefix.isascii() and prefix.isdigit())
        ):
            self._fail("Invalid Guacamole element length")

    def _fail(self, message: str) -> Never:
        self._buffer = ""
        raise GuacamoleProtocolError(message)

    def split_internal(self, instructions: list[tuple[str, list[str]]]) -> tuple[list[str], str]:
        """Split parsed instructions into tunnel ping responses and data to forward to guacd."""
        responses: list[str] = []
        forwarded: list[str] = []
        for raw, elements in instructions:
            if elements[0]:
                forwarded.append(raw)
                continue
            # Instructions with an empty opcode are internal to the tunnel and hidden from
            # guacd; Guacamole.WebSocketTunnel pings are answered by the tunnel endpoint.
            if len(elements) >= PING_ELEMENT_COUNT and elements[1] == "ping":
                responses.append(raw)
        return responses, "".join(forwarded)
