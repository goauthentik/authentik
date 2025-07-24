from unittest import TestCase

from authentik.sources.scim.constants import (
    SCIM_URN_GROUP,
    SCIM_URN_SCHEMA,
    SCIM_URN_USER,
    SCIM_URN_USER_ENTERPRISE,
)
from authentik.sources.scim.patch.lexer import SCIMPathLexer, Token, TokenType


class TestTokenType(TestCase):
    """Test TokenType enum"""

    def test_token_type_values(self):
        """Test that all token types have correct values"""
        self.assertEqual(TokenType.ATTRIBUTE.value, "ATTRIBUTE")
        self.assertEqual(TokenType.DOT.value, "DOT")
        self.assertEqual(TokenType.LBRACKET.value, "LBRACKET")
        self.assertEqual(TokenType.RBRACKET.value, "RBRACKET")
        self.assertEqual(TokenType.LPAREN.value, "LPAREN")
        self.assertEqual(TokenType.RPAREN.value, "RPAREN")
        self.assertEqual(TokenType.STRING.value, "STRING")
        self.assertEqual(TokenType.NUMBER.value, "NUMBER")
        self.assertEqual(TokenType.BOOLEAN.value, "BOOLEAN")
        self.assertEqual(TokenType.NULL.value, "NULL")
        self.assertEqual(TokenType.OPERATOR.value, "OPERATOR")
        self.assertEqual(TokenType.AND.value, "AND")
        self.assertEqual(TokenType.OR.value, "OR")
        self.assertEqual(TokenType.NOT.value, "NOT")
        self.assertEqual(TokenType.EOF.value, "EOF")


class TestToken(TestCase):
    """Test Token dataclass"""

    def test_token_creation(self):
        """Test token creation with all parameters"""
        token = Token(TokenType.ATTRIBUTE, "userName", 5)
        self.assertEqual(token.type, TokenType.ATTRIBUTE)
        self.assertEqual(token.value, "userName")
        self.assertEqual(token.position, 5)

    def test_token_creation_default_position(self):
        """Test token creation with default position"""
        token = Token(TokenType.DOT, ".")
        self.assertEqual(token.type, TokenType.DOT)
        self.assertEqual(token.value, ".")
        self.assertEqual(token.position, 0)


class TestSCIMPathLexer(TestCase):
    """Test SCIMPathLexer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.simple_lexer = SCIMPathLexer("userName")

    def test_init(self):
        """Test lexer initialization"""
        lexer = SCIMPathLexer("test")
        self.assertEqual(lexer.text, "test")
        self.assertEqual(lexer.pos, 0)
        self.assertEqual(lexer.current_char, "t")
        self.assertIn(SCIM_URN_SCHEMA, lexer.schema_urns)
        self.assertIn(SCIM_URN_GROUP, lexer.schema_urns)
        self.assertIn(SCIM_URN_USER, lexer.schema_urns)
        self.assertIn(SCIM_URN_USER_ENTERPRISE, lexer.schema_urns)
        self.assertEqual(
            lexer.OPERATORS, ["eq", "ne", "co", "sw", "ew", "gt", "lt", "ge", "le", "pr"]
        )

    def test_init_empty_string(self):
        """Test lexer initialization with empty string"""
        lexer = SCIMPathLexer("")
        self.assertEqual(lexer.text, "")
        self.assertEqual(lexer.pos, 0)
        self.assertIsNone(lexer.current_char)

    def test_advance(self):
        """Test advance method"""
        lexer = SCIMPathLexer("abc")
        self.assertEqual(lexer.current_char, "a")

        lexer.advance()
        self.assertEqual(lexer.pos, 1)
        self.assertEqual(lexer.current_char, "b")

        lexer.advance()
        self.assertEqual(lexer.pos, 2)
        self.assertEqual(lexer.current_char, "c")

        lexer.advance()
        self.assertEqual(lexer.pos, 3)
        self.assertIsNone(lexer.current_char)

    def test_skip_whitespace(self):
        """Test skip_whitespace method"""
        lexer = SCIMPathLexer("   \t\n  abc")
        lexer.skip_whitespace()
        self.assertEqual(lexer.current_char, "a")

    def test_skip_whitespace_only_whitespace(self):
        """Test skip_whitespace with only whitespace"""
        lexer = SCIMPathLexer("   \t\n  ")
        lexer.skip_whitespace()
        self.assertIsNone(lexer.current_char)

    def test_skip_whitespace_no_whitespace(self):
        """Test skip_whitespace with no leading whitespace"""
        lexer = SCIMPathLexer("abc")
        original_pos = lexer.pos
        lexer.skip_whitespace()
        self.assertEqual(lexer.pos, original_pos)
        self.assertEqual(lexer.current_char, "a")

    def test_read_string_double_quotes(self):
        """Test reading double-quoted string"""
        lexer = SCIMPathLexer('"hello world"')
        result = lexer.read_string('"')
        self.assertEqual(result, "hello world")
        self.assertIsNone(lexer.current_char)  # Should be at end

    def test_read_string_single_quotes(self):
        """Test reading single-quoted string"""
        lexer = SCIMPathLexer("'hello world'")
        result = lexer.read_string("'")
        self.assertEqual(result, "hello world")
        self.assertIsNone(lexer.current_char)

    def test_read_string_with_escapes(self):
        """Test reading string with escape characters"""
        lexer = SCIMPathLexer('"hello \\"world\\""')
        result = lexer.read_string('"')
        self.assertEqual(result, 'hello "world"')

    def test_read_string_with_backslash_at_end(self):
        """Test reading string with backslash at end"""
        lexer = SCIMPathLexer('"hello\\"')
        result = lexer.read_string('"')
        self.assertEqual(result, 'hello"')

    def test_read_string_unclosed(self):
        """Test reading unclosed string"""
        lexer = SCIMPathLexer('"hello world')
        result = lexer.read_string('"')
        self.assertEqual(result, "hello world")
        self.assertIsNone(lexer.current_char)

    def test_read_string_empty(self):
        """Test reading empty string"""
        lexer = SCIMPathLexer('""')
        result = lexer.read_string('"')
        self.assertEqual(result, "")

    def test_read_number_integer(self):
        """Test reading integer number"""
        lexer = SCIMPathLexer("123")
        result = lexer.read_number()
        self.assertEqual(result, "123")
        self.assertIsNone(lexer.current_char)

    def test_read_number_float(self):
        """Test reading float number"""
        lexer = SCIMPathLexer("123.456")
        result = lexer.read_number()
        self.assertEqual(result, "123.456")
        self.assertIsNone(lexer.current_char)

    def test_read_number_with_multiple_dots(self):
        """Test reading number with multiple dots (invalid but handled)"""
        lexer = SCIMPathLexer("123.456.789")
        result = lexer.read_number()
        self.assertEqual(result, "123.456.789")
        self.assertIsNone(lexer.current_char)

    def test_read_number_starting_with_dot(self):
        """Test reading number starting with dot"""
        lexer = SCIMPathLexer(".123")
        result = lexer.read_number()
        self.assertEqual(result, ".123")

    def test_read_identifier_simple(self):
        """Test reading simple identifier"""
        lexer = SCIMPathLexer("userName")
        result = lexer.read_identifier()
        self.assertEqual(result, "userName")
        self.assertIsNone(lexer.current_char)

    def test_read_identifier_with_underscore(self):
        """Test reading identifier with underscore"""
        lexer = SCIMPathLexer("user_name")
        result = lexer.read_identifier()
        self.assertEqual(result, "user_name")

    def test_read_identifier_with_hyphen(self):
        """Test reading identifier with hyphen"""
        lexer = SCIMPathLexer("user-name")
        result = lexer.read_identifier()
        self.assertEqual(result, "user-name")

    def test_read_identifier_with_colon(self):
        """Test reading identifier with colon (URN format)"""
        lexer = SCIMPathLexer("urn:ietf:params:scim:schemas:core:2.0:User")
        result = lexer.read_identifier()
        self.assertEqual(result, "urn:ietf:params:scim:schemas:core:2.0:User")

    def test_read_identifier_schema_urn(self):
        """Test reading schema URN identifier"""
        lexer = SCIMPathLexer(f"{SCIM_URN_USER}.userName")
        result = lexer.read_identifier()
        self.assertEqual(result, SCIM_URN_USER)
        self.assertEqual(lexer.current_char, ".")  # Should stop at dot and set current_char to dot

    def test_read_identifier_with_version_number(self):
        """Test reading identifier with version number (dots followed by digits)"""
        lexer = SCIMPathLexer("urn:ietf:params:scim:schemas:core:2.0:User")
        result = lexer.read_identifier()
        self.assertEqual(result, "urn:ietf:params:scim:schemas:core:2.0:User")

    def test_read_identifier_partial_urn_match(self):
        """Test reading identifier that partially matches URN"""
        lexer = SCIMPathLexer("urn:ietf:params:scim:schemas:core:2.0:CustomUser")
        result = lexer.read_identifier()
        self.assertEqual(result, "urn:ietf:params:scim:schemas:core:2.0:CustomUser")

    # Test get_next_token method
    def test_get_next_token_dot(self):
        """Test tokenizing dot"""
        lexer = SCIMPathLexer(".")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.DOT)
        self.assertEqual(token.value, ".")

    def test_get_next_token_lbracket(self):
        """Test tokenizing left bracket"""
        lexer = SCIMPathLexer("[")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.LBRACKET)
        self.assertEqual(token.value, "[")

    def test_get_next_token_rbracket(self):
        """Test tokenizing right bracket"""
        lexer = SCIMPathLexer("]")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.RBRACKET)
        self.assertEqual(token.value, "]")

    def test_get_next_token_lparen(self):
        """Test tokenizing left parenthesis"""
        lexer = SCIMPathLexer("(")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.LPAREN)
        self.assertEqual(token.value, "(")

    def test_get_next_token_rparen(self):
        """Test tokenizing right parenthesis"""
        lexer = SCIMPathLexer(")")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.RPAREN)
        self.assertEqual(token.value, ")")

    def test_get_next_token_string_double_quotes(self):
        """Test tokenizing double-quoted string"""
        lexer = SCIMPathLexer('"test string"')
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.STRING)
        self.assertEqual(token.value, "test string")

    def test_get_next_token_string_single_quotes(self):
        """Test tokenizing single-quoted string"""
        lexer = SCIMPathLexer("'test string'")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.STRING)
        self.assertEqual(token.value, "test string")

    def test_get_next_token_number_integer(self):
        """Test tokenizing integer"""
        lexer = SCIMPathLexer("123")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.NUMBER)
        self.assertEqual(token.value, "123")

    def test_get_next_token_number_float(self):
        """Test tokenizing float"""
        lexer = SCIMPathLexer("123.45")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.NUMBER)
        self.assertEqual(token.value, "123.45")

    def test_get_next_token_boolean_true(self):
        """Test tokenizing boolean true"""
        lexer = SCIMPathLexer("true")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.BOOLEAN)
        self.assertTrue(token.value)

    def test_get_next_token_boolean_false(self):
        """Test tokenizing boolean false"""
        lexer = SCIMPathLexer("false")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.BOOLEAN)
        self.assertFalse(token.value)

    def test_get_next_token_boolean_case_insensitive(self):
        """Test tokenizing boolean with different cases"""
        for value in ["TRUE", "True", "FALSE", "False"]:
            with self.subTest(value=value):
                lexer = SCIMPathLexer(value)
                token = lexer.get_next_token()
                self.assertEqual(token.type, TokenType.BOOLEAN)

    def test_get_next_token_null(self):
        """Test tokenizing null"""
        lexer = SCIMPathLexer("null")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.NULL)
        self.assertIsNone(token.value)

    def test_get_next_token_null_case_insensitive(self):
        """Test tokenizing null with different cases"""
        for value in ["NULL", "Null"]:
            with self.subTest(value=value):
                lexer = SCIMPathLexer(value)
                token = lexer.get_next_token()
                self.assertEqual(token.type, TokenType.NULL)

    def test_get_next_token_and(self):
        """Test tokenizing AND operator"""
        lexer = SCIMPathLexer("and")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.AND)
        self.assertEqual(token.value, "and")

    def test_get_next_token_or(self):
        """Test tokenizing OR operator"""
        lexer = SCIMPathLexer("or")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.OR)
        self.assertEqual(token.value, "or")

    def test_get_next_token_not(self):
        """Test tokenizing NOT operator"""
        lexer = SCIMPathLexer("not")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.NOT)
        self.assertEqual(token.value, "not")

    def test_get_next_token_operators(self):
        """Test tokenizing all comparison operators"""
        operators = ["eq", "ne", "co", "sw", "ew", "gt", "lt", "ge", "le", "pr"]
        for op in operators:
            with self.subTest(operator=op):
                lexer = SCIMPathLexer(op)
                token = lexer.get_next_token()
                self.assertEqual(token.type, TokenType.OPERATOR)
                self.assertEqual(token.value, op)

    def test_get_next_token_operators_case_insensitive(self):
        """Test tokenizing operators with different cases"""
        for op in ["EQ", "Eq", "NE", "Ne"]:
            with self.subTest(operator=op):
                lexer = SCIMPathLexer(op)
                token = lexer.get_next_token()
                self.assertEqual(token.type, TokenType.OPERATOR)
                self.assertEqual(token.value, op.lower())

    def test_get_next_token_attribute(self):
        """Test tokenizing attribute name"""
        lexer = SCIMPathLexer("userName")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.ATTRIBUTE)
        self.assertEqual(token.value, "userName")

    def test_get_next_token_attribute_with_underscore(self):
        """Test tokenizing attribute name with underscore"""
        lexer = SCIMPathLexer("_userName")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.ATTRIBUTE)
        self.assertEqual(token.value, "_userName")

    def test_get_next_token_eof(self):
        """Test tokenizing end of file"""
        lexer = SCIMPathLexer("")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.EOF)
        self.assertEqual(token.value, "")

    def test_get_next_token_with_whitespace(self):
        """Test tokenizing with leading whitespace"""
        lexer = SCIMPathLexer("   userName")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.ATTRIBUTE)
        self.assertEqual(token.value, "userName")

    def test_get_next_token_skip_unknown_characters(self):
        """Test that unknown characters are skipped"""
        lexer = SCIMPathLexer("@#$userName")
        token = lexer.get_next_token()
        self.assertEqual(token.type, TokenType.ATTRIBUTE)
        self.assertEqual(token.value, "userName")

    def test_get_next_token_multiple_tokens(self):
        """Test tokenizing multiple tokens in sequence"""
        lexer = SCIMPathLexer("userName.givenName")

        token1 = lexer.get_next_token()
        self.assertEqual(token1.type, TokenType.ATTRIBUTE)
        self.assertEqual(token1.value, "userName")

        token2 = lexer.get_next_token()
        self.assertEqual(token2.type, TokenType.DOT)
        self.assertEqual(token2.value, ".")

        token3 = lexer.get_next_token()
        self.assertEqual(token3.type, TokenType.ATTRIBUTE)
        self.assertEqual(token3.value, "givenName")

        token4 = lexer.get_next_token()
        self.assertEqual(token4.type, TokenType.EOF)

    def test_get_next_token_complex_filter(self):
        """Test tokenizing complex filter expression"""
        lexer = SCIMPathLexer('emails[type eq "work" and primary eq true]')

        tokens = []
        while True:
            token = lexer.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break

        expected_types = [
            TokenType.ATTRIBUTE,  # emails
            TokenType.LBRACKET,  # [
            TokenType.ATTRIBUTE,  # type
            TokenType.OPERATOR,  # eq
            TokenType.STRING,  # "work"
            TokenType.AND,  # and
            TokenType.ATTRIBUTE,  # primary
            TokenType.OPERATOR,  # eq
            TokenType.BOOLEAN,  # true
            TokenType.RBRACKET,  # ]
            TokenType.EOF,
        ]

        self.assertEqual(len(tokens), len(expected_types))
        for token, expected_type in zip(tokens, expected_types, strict=False):
            self.assertEqual(token.type, expected_type)

    def test_get_next_token_urn_attribute(self):
        """Test tokenizing URN-based attribute"""
        lexer = SCIMPathLexer(f"{SCIM_URN_USER}.userName")

        token1 = lexer.get_next_token()
        self.assertEqual(token1.type, TokenType.ATTRIBUTE)
        self.assertEqual(token1.value, SCIM_URN_USER)

        token2 = lexer.get_next_token()
        self.assertEqual(token2.type, TokenType.DOT)

        token3 = lexer.get_next_token()
        self.assertEqual(token3.type, TokenType.ATTRIBUTE)
        self.assertEqual(token3.value, "userName")

    def test_get_next_token_enterprise_urn(self):
        """Test tokenizing enterprise URN"""
        lexer = SCIMPathLexer(f"{SCIM_URN_USER_ENTERPRISE}.manager")

        token1 = lexer.get_next_token()
        self.assertEqual(token1.type, TokenType.ATTRIBUTE)
        self.assertEqual(token1.value, SCIM_URN_USER_ENTERPRISE)

        token2 = lexer.get_next_token()
        self.assertEqual(token2.type, TokenType.DOT)

    def test_lexer_state_after_eof(self):
        """Test lexer state after reaching EOF"""
        lexer = SCIMPathLexer("a")

        # Get first token
        token1 = lexer.get_next_token()
        self.assertEqual(token1.type, TokenType.ATTRIBUTE)

        # Get EOF token
        token2 = lexer.get_next_token()
        self.assertEqual(token2.type, TokenType.EOF)

        # Should continue returning EOF
        token3 = lexer.get_next_token()
        self.assertEqual(token3.type, TokenType.EOF)

    def test_read_identifier_edge_cases(self):
        """Test read_identifier with edge cases"""
        # Test identifier ending with colon
        lexer = SCIMPathLexer("test:")
        result = lexer.read_identifier()
        self.assertEqual(result, "test:")

        # Test identifier with numbers
        lexer = SCIMPathLexer("test123")
        result = lexer.read_identifier()
        self.assertEqual(result, "test123")

    def test_complex_urn_parsing(self):
        """Test parsing complex URN with version numbers"""
        urn = "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User"
        lexer = SCIMPathLexer(urn)
        result = lexer.read_identifier()
        self.assertEqual(result, urn)
