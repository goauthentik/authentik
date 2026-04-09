from django.test import TestCase
from pydantic import ValidationError

from authentik.providers.scim.clients.schema import Email


class TestSCIMSchema(TestCase):
    def test_email(self):
        """Ensure that email addresses that validate in django validate in SCIM"""
        Email.model_validate({"value": "foo@bar.com"})
        Email.model_validate({"value": "username@testipa.local"})
        with self.assertRaises(ValidationError):
            Email.model_validate({"value": "username"})
