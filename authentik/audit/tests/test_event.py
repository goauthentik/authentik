"""audit event tests"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.audit.models import Event
from authentik.policies.dummy.models import DummyPolicy


class TestAuditEvent(TestCase):
    """Test Audit Event"""

    def test_new_with_model(self):
        """Create a new Event passing a model as kwarg"""
        event = Event.new("unittest", test={"model": get_anonymous_user()})
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(get_anonymous_user())
        self.assertEqual(
            event.context.get("test").get("model").get("app"),
            model_content_type.app_label,
        )

    def test_new_with_uuid_model(self):
        """Create a new Event passing a model (with UUID PK) as kwarg"""
        temp_model = DummyPolicy.objects.create(name="test", result=True)
        event = Event.new("unittest", model=temp_model)
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(temp_model)
        self.assertEqual(
            event.context.get("model").get("app"), model_content_type.app_label
        )
        self.assertEqual(event.context.get("model").get("pk"), temp_model.pk.hex)
