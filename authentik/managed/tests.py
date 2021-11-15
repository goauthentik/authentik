"""managed tests"""
from django.test import TestCase

from authentik.managed.tasks import managed_reconcile


class TestManaged(TestCase):
    """managed tests"""

    def test_reconcile(self):
        """Test reconcile"""
        # pyright: reportGeneralTypeIssues=false
        managed_reconcile()  # pylint: disable=no-value-for-parameter
