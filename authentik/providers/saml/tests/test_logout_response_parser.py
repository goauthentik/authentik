"""logout response tests"""

import tracemalloc

from django.test import SimpleTestCase

from authentik.common.saml.exceptions import CannotHandleAssertion
from authentik.common.saml.parsers.logout_response import LogoutResponseParser
from authentik.providers.saml.utils.encoding import deflate_and_base64_encode


class TestLogoutResponse(SimpleTestCase):
    """Test LogoutResponse parser"""

    def test_redirect_over_size_limit(self):
        """Test that a redirect-binding response that inflates beyond the size limit is refused"""
        response = deflate_and_base64_encode(
            '<samlp:LogoutResponse xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            'ID="_1" Version="2.0" IssueInstant="2022-02-21T22:50:33.999Z"/>'
            + " " * (32 * 1024 * 1024)
        )

        tracemalloc.start()
        self.addCleanup(tracemalloc.stop)
        with self.assertRaises(CannotHandleAssertion):
            LogoutResponseParser().parse_detached(response)
        _, peak = tracemalloc.get_traced_memory()

        self.assertLess(peak, 32 * 1024 * 1024)
