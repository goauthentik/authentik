from typing import Any

from authentik.sources.scim.patch.lexer import SCIMPathLexer, TokenType


class SCIMPathParser:
    """Parser for SCIM paths including filter expressions"""

    def __init__(self):
        self.lexer = None
        self.current_token = None

    def parse_path(self, path: str | None) -> list[dict[str, Any]]:
        """Parse a SCIM path into components"""
        self.lexer = SCIMPathLexer(path)
        self.current_token = self.lexer.get_next_token()

        components = []

        while self.current_token.type != TokenType.EOF:
            component = self._parse_path_component()
            if component:
                components.append(component)

        return components

    def _parse_path_component(self) -> dict[str, Any] | None:
        """Parse a single path component"""
        if self.current_token.type != TokenType.ATTRIBUTE:
            return None

        attribute = self.current_token.value
        self._consume(TokenType.ATTRIBUTE)

        filter_expr = None
        sub_attribute = None

        # Check for filter expression
        if self.current_token.type == TokenType.LBRACKET:
            self._consume(TokenType.LBRACKET)
            filter_expr = self._parse_filter_expression()
            self._consume(TokenType.RBRACKET)

        # Check for sub-attribute
        if self.current_token.type == TokenType.DOT:
            self._consume(TokenType.DOT)
            if self.current_token.type == TokenType.ATTRIBUTE:
                sub_attribute = self.current_token.value
                self._consume(TokenType.ATTRIBUTE)

        return {"attribute": attribute, "filter": filter_expr, "sub_attribute": sub_attribute}

    def _parse_filter_expression(self) -> dict[str, Any] | None:
        """Parse a filter expression like 'primary eq true' or
        'type eq "work" and primary eq true'"""
        return self._parse_or_expression()

    def _parse_or_expression(self) -> dict[str, Any] | None:
        """Parse OR expressions"""
        left = self._parse_and_expression()

        while self.current_token.type == TokenType.OR:
            self._consume(TokenType.OR)
            right = self._parse_and_expression()
            left = {"type": "logical", "operator": "or", "left": left, "right": right}

        return left

    def _parse_and_expression(self) -> dict[str, Any] | None:
        """Parse AND expressions"""
        left = self._parse_primary_expression()

        while self.current_token.type == TokenType.AND:
            self._consume(TokenType.AND)
            right = self._parse_primary_expression()
            left = {"type": "logical", "operator": "and", "left": left, "right": right}

        return left

    def _parse_primary_expression(self) -> dict[str, Any] | None:
        """Parse primary expressions (attribute operator value)"""
        if self.current_token.type == TokenType.LPAREN:
            self._consume(TokenType.LPAREN)
            expr = self._parse_or_expression()
            self._consume(TokenType.RPAREN)
            return expr

        if self.current_token.type == TokenType.NOT:
            self._consume(TokenType.NOT)
            expr = self._parse_primary_expression()
            return {"type": "logical", "operator": "not", "operand": expr}

        if self.current_token.type != TokenType.ATTRIBUTE:
            return None

        attribute = self.current_token.value
        self._consume(TokenType.ATTRIBUTE)

        if self.current_token.type != TokenType.OPERATOR:
            return None

        operator = self.current_token.value
        self._consume(TokenType.OPERATOR)

        # Parse value
        value = None
        if self.current_token.type == TokenType.STRING:
            value = self.current_token.value
            self._consume(TokenType.STRING)
        elif self.current_token.type == TokenType.NUMBER:
            value = (
                float(self.current_token.value)
                if "." in self.current_token.value
                else int(self.current_token.value)
            )
            self._consume(TokenType.NUMBER)
        elif self.current_token.type == TokenType.BOOLEAN:
            value = self.current_token.value
            self._consume(TokenType.BOOLEAN)
        elif self.current_token.type == TokenType.NULL:
            value = None
            self._consume(TokenType.NULL)

        return {"type": "comparison", "attribute": attribute, "operator": operator, "value": value}

    def _consume(self, expected_type: TokenType):
        """Consume a token of the expected type"""
        if self.current_token.type == expected_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise ValueError(f"Expected {expected_type}, got {self.current_token.type}")
