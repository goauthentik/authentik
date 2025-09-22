from dataclasses import dataclass
from enum import Enum

from authentik.sources.scim.constants import (
    SCIM_URN_GROUP,
    SCIM_URN_SCHEMA,
    SCIM_URN_USER,
    SCIM_URN_USER_ENTERPRISE,
)


# Token types for SCIM path parsing
class TokenType(Enum):
    ATTRIBUTE = "ATTRIBUTE"
    DOT = "DOT"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    NULL = "NULL"
    OPERATOR = "OPERATOR"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int = 0


class SCIMPathLexer:
    """Lexer for SCIM paths and filter expressions"""

    OPERATORS = ["eq", "ne", "co", "sw", "ew", "gt", "lt", "ge", "le", "pr"]

    def __init__(self, text: str):
        self.schema_urns = [
            SCIM_URN_SCHEMA,
            SCIM_URN_GROUP,
            SCIM_URN_USER,
            SCIM_URN_USER_ENTERPRISE,
        ]
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def advance(self):
        """Move to next character"""
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def read_string(self, quote_char):
        """Read a quoted string"""
        value = ""
        self.advance()  # Skip opening quote

        while self.current_char and self.current_char != quote_char:
            if self.current_char == "\\":
                self.advance()
                if self.current_char:
                    value += self.current_char
                    self.advance()
            else:
                value += self.current_char
                self.advance()

        if self.current_char == quote_char:
            self.advance()  # Skip closing quote

        return value

    def read_number(self):
        """Read a number (integer or float)"""
        value = ""
        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            value += self.current_char
            self.advance()
        return value

    def read_identifier(self):
        """Read an identifier (attribute name or operator) - supports URN format"""
        value = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char in "_-:"):
            value += self.current_char
            self.advance()
            # If the identifier value so far is a schema URN, take that as the identifier and
            # treat the next part as a sub_attribute
            if value in self.schema_urns:
                self.current_char = "."
                return value

            # Handle dots within URN identifiers (like "2.0")
            # A dot is part of the identifier if it's followed by a digit
            if (
                self.current_char == "."
                and self.pos + 1 < len(self.text)
                and self.text[self.pos + 1].isdigit()
            ):
                value += self.current_char
                self.advance()
                # Continue reading digits after the dot
                while self.current_char and self.current_char.isdigit():
                    value += self.current_char
                    self.advance()

        return value

    def get_next_token(self) -> Token:  # noqa PLR0911
        """Get the next token from the input"""
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == ".":
                self.advance()
                return Token(TokenType.DOT, ".")

            if self.current_char == "[":
                self.advance()
                return Token(TokenType.LBRACKET, "[")

            if self.current_char == "]":
                self.advance()
                return Token(TokenType.RBRACKET, "]")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(")

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")")

            if self.current_char in "\"'":
                quote_char = self.current_char
                value = self.read_string(quote_char)
                return Token(TokenType.STRING, value)

            if self.current_char.isdigit():
                value = self.read_number()
                return Token(TokenType.NUMBER, value)

            if self.current_char.isalpha() or self.current_char == "_":
                value = self.read_identifier()

                # Check for special keywords
                if value.lower() == "true":
                    return Token(TokenType.BOOLEAN, True)
                elif value.lower() == "false":
                    return Token(TokenType.BOOLEAN, False)
                elif value.lower() == "null":
                    return Token(TokenType.NULL, None)
                elif value.lower() == "and":
                    return Token(TokenType.AND, "and")
                elif value.lower() == "or":
                    return Token(TokenType.OR, "or")
                elif value.lower() == "not":
                    return Token(TokenType.NOT, "not")
                elif value.lower() in self.OPERATORS:
                    return Token(TokenType.OPERATOR, value.lower())
                else:
                    return Token(TokenType.ATTRIBUTE, value)

            # Skip unknown characters
            self.advance()

        return Token(TokenType.EOF, "")
