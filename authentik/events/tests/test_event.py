"""event tests"""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from guardian.shortcuts import get_anonymous_user

from authentik.core.models import Group
from authentik.events.models import Event
from authentik.policies.dummy.models import DummyPolicy


class TestEvents(TestCase):
    """Test Event"""

    def test_new_with_model(self):
        """Create a new Event passing a model as kwarg"""
        test_model = Group.objects.create(name="test")
        event = Event.new("unittest", test={"model": test_model})
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(test_model)
        self.assertEqual(
            event.context.get("test").get("model").get("app"),
            model_content_type.app_label,
        )

    def test_new_with_user(self):
        """Create a new Event passing a user as kwarg"""
        event = Event.new("unittest", test={"model": get_anonymous_user()})
        event.save()  # We save to ensure nothing is un-saveable
        self.assertEqual(
            event.context.get("test").get("model").get("username"),
            get_anonymous_user().username,
        )

    def test_new_with_uuid_model(self):
        """Create a new Event passing a model (with UUID PK) as kwarg"""
        temp_model = DummyPolicy.objects.create(name="test", result=True)
        event = Event.new("unittest", model=temp_model)
        event.save()  # We save to ensure nothing is un-saveable
        model_content_type = ContentType.objects.get_for_model(temp_model)
        self.assertEqual(event.context.get("model").get("app"), model_content_type.app_label)
        self.assertEqual(event.context.get("model").get("pk"), temp_model.pk.hex)
