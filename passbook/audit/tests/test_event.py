"""audit event tests"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from passbook.audit.models import Event, EventAction
from passbook.core.models import Policy


class TestAuditEvent(TestCase):
    """Test Audit Event"""

    def test_new_with_model(self):
        """Create a new Event passing a model as kwarg"""
        event = Event.new(EventAction.CUSTOM, test={"model": get_anonymous_user()})
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(get_anonymous_user())
        self.assertEqual(
            event.context.get("test").get("model").get("app"),
            model_content_type.app_label,
        )

    def test_new_with_uuid_model(self):
        """Create a new Event passing a model (with UUID PK) as kwarg"""
        temp_model = Policy.objects.create()
        event = Event.new(EventAction.CUSTOM, model=temp_model)
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(temp_model)
        self.assertEqual(
            event.context.get("model").get("app"), model_content_type.app_label
        )
        self.assertEqual(event.context.get("model").get("pk"), temp_model.pk.hex)
