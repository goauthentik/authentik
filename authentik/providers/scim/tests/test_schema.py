from django.test import TestCase
from pydantic import ValidationError

from authentik.providers.scim.clients.schema import Email, EnterpriseUser


class TestSCIMSchema(TestCase):
    def test_email(self):
        """Ensure that email addresses that validate in django validate in SCIM"""
        Email.model_validate({"value": "foo@bar.com"})
        Email.model_validate({"value": "username@testipa.local"})
        with self.assertRaises(ValidationError):
            Email.model_validate({"value": "username"})

    def test_slack_manager_id_value(self):
        """Ensure Manager Id is exposed as "value" and "managerId" [for slack]"""
        manager = "Ua123561"
        raw_enterprise_user = {
            "division": "ITPE - INS",
            "department": "Finance, IT, Procurement & IR",
            "costCenter": "212380006",
            "employeeNumber": "77002753",
            "organization": "Finance, IT, Procurement & IR",
            "manager": {"managerId": manager},
        }
        result = EnterpriseUser.model_validate(raw_enterprise_user)
        assert manager == result.manager.managerId, "managerId was not propagated"

        raw_enterprise_user["manager"] = {"value": manager}
        result = EnterpriseUser.model_validate(raw_enterprise_user)
        assert manager == result.manager.value, "value was not propagated"
