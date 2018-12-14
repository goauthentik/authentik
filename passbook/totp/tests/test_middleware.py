"""passbook TOTP Middleware Test"""

import os

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from passbook.core.views import overview
from passbook.totp.middleware import totp_force_verify


class TestMiddleware(TestCase):
    """passbook TOTP Middleware Test"""

    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = 'True'
        self.factory = RequestFactory()

    def test_totp_force_verify_anon(self):
        """Test Anonymous TFA Force"""
        request = self.factory.get(reverse('passbook_core:overview'))
        request.user = AnonymousUser()
        response = totp_force_verify(overview.OverviewView.as_view())(request)
        self.assertEqual(response.status_code, 302)
