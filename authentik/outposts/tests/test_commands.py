"""management command tests"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class TestManagementCommands(TestCase):
    """management command tests"""

    def test_repair_permissions(self):
        """Test repair_permissions"""
        out = StringIO()
        call_command("repair_permissions", stdout=out)
        self.assertNotEqual(out.getvalue(), "")
