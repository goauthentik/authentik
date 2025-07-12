from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class PatchOperation(Enum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"


@dataclass
class PatchOp:
    op: PatchOperation
    path: str
    value: Any = None


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

    OPERATORS = ['eq', 'ne', 'co', 'sw', 'ew', 'gt', 'lt', 'ge', 'le', 'pr']

    def __init__(self, text: str):
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
            if self.current_char == '\\':
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
        while self.current_char and (self.current_char.isdigit() or self.current_char == '.'):
            value += self.current_char
            self.advance()
        return value

    def read_identifier(self):
        """Read an identifier (attribute name or operator)"""
        value = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char in '_-'):
            value += self.current_char
            self.advance()
        return value

    def get_next_token(self) -> Token:
        """Get the next token from the input"""
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char == '.':
                self.advance()
                return Token(TokenType.DOT, '.')

            if self.current_char == '[':
                self.advance()
                return Token(TokenType.LBRACKET, '[')

            if self.current_char == ']':
                self.advance()
                return Token(TokenType.RBRACKET, ']')

            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN, '(')

            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN, ')')

            if self.current_char in '"\'':
                quote_char = self.current_char
                value = self.read_string(quote_char)
                return Token(TokenType.STRING, value)

            if self.current_char.isdigit():
                value = self.read_number()
                return Token(TokenType.NUMBER, value)

            if self.current_char.isalpha() or self.current_char == '_':
                value = self.read_identifier()

                # Check for special keywords
                if value.lower() == 'true':
                    return Token(TokenType.BOOLEAN, True)
                elif value.lower() == 'false':
                    return Token(TokenType.BOOLEAN, False)
                elif value.lower() == 'null':
                    return Token(TokenType.NULL, None)
                elif value.lower() == 'and':
                    return Token(TokenType.AND, 'and')
                elif value.lower() == 'or':
                    return Token(TokenType.OR, 'or')
                elif value.lower() == 'not':
                    return Token(TokenType.NOT, 'not')
                elif value.lower() in self.OPERATORS:
                    return Token(TokenType.OPERATOR, value.lower())
                else:
                    return Token(TokenType.ATTRIBUTE, value)

            # Skip unknown characters
            self.advance()

        return Token(TokenType.EOF, '')


class SCIMPathParser:
    """Parser for SCIM paths including filter expressions"""

    def __init__(self):
        self.lexer = None
        self.current_token = None

    def parse_path(self, path: str) -> List[Dict[str, Any]]:
        """Parse a SCIM path into components"""
        self.lexer = SCIMPathLexer(path)
        self.current_token = self.lexer.get_next_token()

        components = []

        while self.current_token.type != TokenType.EOF:
            component = self._parse_path_component()
            if component:
                components.append(component)

        return components

    def _parse_path_component(self) -> Optional[Dict[str, Any]]:
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

        return {
            'attribute': attribute,
            'filter': filter_expr,
            'sub_attribute': sub_attribute
        }

    def _parse_filter_expression(self) -> Optional[Dict[str, Any]]:
        """Parse a filter expression like 'primary eq true' or 'type eq "work" and primary eq true'"""
        return self._parse_or_expression()

    def _parse_or_expression(self) -> Optional[Dict[str, Any]]:
        """Parse OR expressions"""
        left = self._parse_and_expression()

        while self.current_token.type == TokenType.OR:
            self._consume(TokenType.OR)
            right = self._parse_and_expression()
            left = {
                'type': 'logical',
                'operator': 'or',
                'left': left,
                'right': right
            }

        return left

    def _parse_and_expression(self) -> Optional[Dict[str, Any]]:
        """Parse AND expressions"""
        left = self._parse_primary_expression()

        while self.current_token.type == TokenType.AND:
            self._consume(TokenType.AND)
            right = self._parse_primary_expression()
            left = {
                'type': 'logical',
                'operator': 'and',
                'left': left,
                'right': right
            }

        return left

    def _parse_primary_expression(self) -> Optional[Dict[str, Any]]:
        """Parse primary expressions (attribute operator value)"""
        if self.current_token.type == TokenType.LPAREN:
            self._consume(TokenType.LPAREN)
            expr = self._parse_or_expression()
            self._consume(TokenType.RPAREN)
            return expr

        if self.current_token.type == TokenType.NOT:
            self._consume(TokenType.NOT)
            expr = self._parse_primary_expression()
            return {
                'type': 'logical',
                'operator': 'not',
                'operand': expr
            }

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
            value = float(self.current_token.value) if '.' in self.current_token.value else int(self.current_token.value)
            self._consume(TokenType.NUMBER)
        elif self.current_token.type == TokenType.BOOLEAN:
            value = self.current_token.value
            self._consume(TokenType.BOOLEAN)
        elif self.current_token.type == TokenType.NULL:
            value = None
            self._consume(TokenType.NULL)

        return {
            'type': 'comparison',
            'attribute': attribute,
            'operator': operator,
            'value': value
        }

    def _consume(self, expected_type: TokenType):
        """Consume a token of the expected type"""
        if self.current_token.type == expected_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise ValueError(f"Expected {expected_type}, got {self.current_token.type}")


class SCIMPatchProcessor:
    """Processes SCIM patch operations on Python dictionaries"""

    def __init__(self):
        self.parser = SCIMPathParser()

    def apply_patches(self, data: Dict[str, Any], patches: List[PatchOp]) -> Dict[str, Any]:
        """Apply a list of patch operations to the data"""
        result = data.copy()

        for patch in patches:
            if patch.op == PatchOperation.ADD:
                self._apply_add(result, patch.path, patch.value)
            elif patch.op == PatchOperation.REMOVE:
                self._apply_remove(result, patch.path)
            elif patch.op == PatchOperation.REPLACE:
                self._apply_replace(result, patch.path, patch.value)

        return result

    def _apply_add(self, data: Dict[str, Any], path: str, value: Any):
        """Apply ADD operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]['filter']:
            # Simple path
            attr = components[0]['attribute']
            if components[0]['sub_attribute']:
                if attr not in data:
                    data[attr] = {}
                data[attr][components[0]['sub_attribute']] = value
            else:
                data[attr] = value
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, value, 'add')

    def _apply_remove(self, data: Dict[str, Any], path: str):
        """Apply REMOVE operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]['filter']:
            # Simple path
            attr = components[0]['attribute']
            if components[0]['sub_attribute']:
                if attr in data and isinstance(data[attr], dict):
                    data[attr].pop(components[0]['sub_attribute'], None)
            else:
                data.pop(attr, None)
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, None, 'remove')

    def _apply_replace(self, data: Dict[str, Any], path: str, value: Any):
        """Apply REPLACE operation"""
        components = self.parser.parse_path(path)

        if len(components) == 1 and not components[0]['filter']:
            # Simple path
            attr = components[0]['attribute']
            if components[0]['sub_attribute']:
                if attr not in data:
                    data[attr] = {}
                data[attr][components[0]['sub_attribute']] = value
            else:
                data[attr] = value
        else:
            # Complex path with filters
            self._navigate_and_modify(data, components, value, 'replace')

    def _navigate_and_modify(self, data: Dict[str, Any], components: List[Dict[str, Any]],
                           value: Any, operation: str):
        """Navigate through complex paths and apply modifications"""
        current = data

        for i, component in enumerate(components):
            attr = component['attribute']
            filter_expr = component['filter']
            sub_attr = component['sub_attribute']

            if filter_expr:
                # Handle array with filter
                if attr not in current:
                    if operation == 'add':
                        current[attr] = []
                    else:
                        return

                if not isinstance(current[attr], list):
                    return

                # Find matching items
                matching_items = []
                for item in current[attr]:
                    if self._matches_filter(item, filter_expr):
                        matching_items.append(item)

                if not matching_items and operation == 'add':
                    # Create new item if none match (only for simple comparison filters)
                    if filter_expr.get('type', 'comparison') == 'comparison':
                        new_item = {filter_expr['attribute']: filter_expr['value']}
                        current[attr].append(new_item)
                        matching_items = [new_item]

                # Apply operation to matching items
                for item in matching_items:
                    if sub_attr:
                        if operation == 'add' or operation == 'replace':
                            item[sub_attr] = value
                        elif operation == 'remove':
                            item.pop(sub_attr, None)
                    else:
                        if operation == 'add' or operation == 'replace':
                            if isinstance(value, dict):
                                item.update(value)
                            else:
                                # If value is not a dict, we can't merge it
                                pass
                        elif operation == 'remove':
                            # Remove the entire item
                            if item in current[attr]:
                                current[attr].remove(item)
            else:
                # Handle simple attribute
                if i == len(components) - 1:
                    # Last component
                    if sub_attr:
                        if attr not in current:
                            current[attr] = {}
                        if operation == 'add' or operation == 'replace':
                            current[attr][sub_attr] = value
                        elif operation == 'remove':
                            current[attr].pop(sub_attr, None)
                    else:
                        if operation == 'add' or operation == 'replace':
                            current[attr] = value
                        elif operation == 'remove':
                            current.pop(attr, None)
                else:
                    # Navigate deeper
                    if attr not in current:
                        current[attr] = {}
                    current = current[attr]

    def _matches_filter(self, item: Dict[str, Any], filter_expr: Dict[str, Any]) -> bool:
        """Check if an item matches the filter expression"""
        if not filter_expr:
            return True

        filter_type = filter_expr.get('type', 'comparison')

        if filter_type == 'comparison':
            return self._matches_comparison(item, filter_expr)
        elif filter_type == 'logical':
            return self._matches_logical(item, filter_expr)

        return False

    def _matches_comparison(self, item: Dict[str, Any], filter_expr: Dict[str, Any]) -> bool:
        """Check if an item matches a comparison filter"""
        attr = filter_expr['attribute']
        operator = filter_expr['operator']
        expected_value = filter_expr['value']

        if attr not in item:
            return False

        actual_value = item[attr]

        if operator == 'eq':
            return actual_value == expected_value
        elif operator == 'ne':
            return actual_value != expected_value
        elif operator == 'co':
            return str(expected_value) in str(actual_value)
        elif operator == 'sw':
            return str(actual_value).startswith(str(expected_value))
        elif operator == 'ew':
            return str(actual_value).endswith(str(expected_value))
        elif operator == 'gt':
            return actual_value > expected_value
        elif operator == 'lt':
            return actual_value < expected_value
        elif operator == 'ge':
            return actual_value >= expected_value
        elif operator == 'le':
            return actual_value <= expected_value
        elif operator == 'pr':
            return actual_value is not None

        return False

    def _matches_logical(self, item: Dict[str, Any], filter_expr: Dict[str, Any]) -> bool:
        """Check if an item matches a logical filter expression"""
        operator = filter_expr['operator']

        if operator == 'and':
            left_result = self._matches_filter(item, filter_expr['left'])
            right_result = self._matches_filter(item, filter_expr['right'])
            return left_result and right_result
        elif operator == 'or':
            left_result = self._matches_filter(item, filter_expr['left'])
            right_result = self._matches_filter(item, filter_expr['right'])
            return left_result or right_result
        elif operator == 'not':
            operand_result = self._matches_filter(item, filter_expr['operand'])
            return not operand_result

        return False


# Example usage and testing
if __name__ == "__main__":
    # Sample SCIM user data
    user_data = {
        "id": "user123",
        "userName": "john.doe",
        "name": {
            "formatted": "John Doe",
            "familyName": "Doe",
            "givenName": "John"
        },
        "emails": [
            {
                "value": "john.doe@example.com",
                "type": "work",
                "primary": True
            },
            {
                "value": "john.personal@example.com",
                "type": "personal",
                "primary": False
            }
        ],
        "phoneNumbers": [
            {
                "value": "+1-555-123-4567",
                "type": "work",
                "primary": True
            },
            {
                "value": "+1-555-987-6543",
                "type": "mobile",
                "primary": False
            }
        ],
        "addresses": [
            {
                "streetAddress": "123 Work St",
                "city": "Work City",
                "type": "work",
                "primary": True
            },
            {
                "streetAddress": "456 Home Ave",
                "city": "Home City",
                "type": "home",
                "primary": False
            },
            {
                "streetAddress": "789 Other Rd",
                "city": "Other City",
                "type": "work",
                "primary": False
            }
        ]
    }

    # Create processor
    processor = SCIMPatchProcessor()

    # Example patch operations
    patches = [
        # Replace primary phone number
        PatchOp(
            op=PatchOperation.REPLACE,
            path="phoneNumbers[primary eq true].value",
            value="+1-555-999-0000"
        ),
        # Add new email
        PatchOp(
            op=PatchOperation.ADD,
            path="emails",
            value={
                "value": "john.new@example.com",
                "type": "home",
                "primary": False
            }
        ),
        # Update user's given name
        PatchOp(
            op=PatchOperation.REPLACE,
            path="name.givenName",
            value="Johnny"
        ),
        # Remove work email
        PatchOp(
            op=PatchOperation.REMOVE,
            path="emails[type eq \"work\"]"
        )
    ]

    print("Original data:")
    print(user_data)
    print("\nApplying patches...")

    # Apply patches
    result = processor.apply_patches(user_data, patches)

    print("\nResult after patches:")
    print(result)

    # Test path parsing
    print("\n--- Path Parsing Tests ---")
    test_paths = [
        "userName",
        "name.givenName",
        "emails[primary eq true].value",
        "phoneNumbers[type eq \"work\"].value",
        "addresses[type eq \"work\" and primary eq true].streetAddress"
    ]

    parser = SCIMPathParser()
    for path in test_paths:
        try:
            components = parser.parse_path(path)
            print(f"Path: {path}")
            print(f"  Components: {components}")
        except Exception as e:
            print(f"Path: {path}")
            print(f"  Error: {e}")
        print()
