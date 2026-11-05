"""Bounded JSON parsing"""

import json
import subprocess
import sys

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.bounded_json import (
    is_json_media_type,
    parse_json_object,
)
from authentik.enterprise.providers.oauth2_cimd.errors import InvalidClientMetadata


class TestBoundedJSON(SimpleTestCase):
    """Bounded JSON parsing"""

    def parse(self, content: bytes):
        return parse_json_object(content, InvalidClientMetadata)

    def assertInvalid(self, content: bytes, code: str):
        with self.assertRaises(InvalidClientMetadata) as ctx:
            self.parse(content)
        self.assertEqual(ctx.exception.code, code)

    def test_valid(self):
        self.assertEqual(self.parse(b'{"a": [1, {"b": "[[[["}]}'), {"a": [1, {"b": "[[[["}]})

    def test_depth(self):
        self.parse(json.dumps({"a": [[[[[[{}]]]]]]}).encode())
        self.assertInvalid(b'{"a":' + b"[" * 8 + b"]" * 8 + b"}", "json_too_deep")
        # Would exhaust the recursive parser without the pre-check
        self.assertInvalid(b"[" * 60000 + b"]" * 60000, "json_too_deep")

    def test_brackets_in_strings_ignored(self):
        self.parse(json.dumps({"a": "{" * 100, "b": '\\"[[[[[[[[[[['}).encode())

    def test_unterminated_escaped_quotes_bounded(self):
        script = """
import sys
from authentik.enterprise.providers.oauth2_cimd.bounded_json import parse_json_object
from authentik.enterprise.providers.oauth2_cimd.errors import InvalidClientMetadata
try:
    parse_json_object(sys.stdin.buffer.read(), InvalidClientMetadata)
except InvalidClientMetadata as error:
    assert error.code == 'invalid_json', error.code
else:
    raise AssertionError('Malformed string was accepted')
"""
        for size in (32000, 65000):
            with self.subTest(size=size):
                subprocess.run(
                    [sys.executable, "-c", script],
                    input=b'{"a":"' + b'\\"' * size,
                    capture_output=True,
                    check=True,
                    timeout=3,
                )

    def test_escaped_string_boundaries(self):
        for backslashes in range(8):
            with self.subTest(backslashes=backslashes):
                document = {"string": "\\" * backslashes + '"{}[]', "array": [{}]}
                self.assertEqual(self.parse(json.dumps(document).encode()), document)

    def test_array_size(self):
        self.parse(json.dumps({"a": list(range(64))}).encode())
        self.assertInvalid(json.dumps({"a": list(range(65))}).encode(), "invalid_json")
        self.assertInvalid(json.dumps({"a": {"b": [0] * 65}}).encode(), "invalid_json")

    def test_object_size(self):
        self.assertInvalid(json.dumps({str(i): i for i in range(129)}).encode(), "invalid_json")

    def test_duplicate_members(self):
        self.assertInvalid(b'{"client_id": "a", "client_id": "b"}', "invalid_json")

    def test_non_finite(self):
        for value in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(value=value):
                self.assertInvalid(b'{"a": ' + value + b"}", "invalid_json")

    def test_not_object(self):
        for content in (b"[]", b'"x"', b"1", b"null"):
            with self.subTest(content=content):
                self.assertInvalid(content, "invalid_json")

    def test_encoding(self):
        self.assertInvalid(b'{"a": "\xff"}', "invalid_encoding")
        self.assertInvalid('{"a": 1}'.encode("utf-16"), "invalid_encoding")
        self.assertInvalid(b"", "invalid_json")
        self.assertInvalid(b'{"a": 1} trailing', "invalid_json")

    def test_media_type(self):
        self.assertTrue(is_json_media_type("application/json"))
        self.assertTrue(is_json_media_type("Application/JSON; charset=utf-8"))
        self.assertTrue(is_json_media_type("application/oauth-client-metadata+json"))
        self.assertTrue(is_json_media_type("application/x", "application/x"))
        for value in (None, "", "text/plain", "text/html", "application/javascript", "json"):
            with self.subTest(value=value):
                self.assertFalse(is_json_media_type(value))
