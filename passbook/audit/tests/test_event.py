"""audit event tests"""

from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.audit.models import Event, EventAction


class TestAuditEvent(TestCase):
    """Test Audit Event"""

    def test_new_with_model(self):
        """Create a new Event passing a model as kwarg"""
        event = Event.new(EventAction.CUSTOM, model=get_anonymous_user())
        event.save()
        self.assertIsNotNone(event.pk)
