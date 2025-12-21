from django.test import TestCase

from akql.queryset import apply_search
from authentik.core.tests.utils import create_test_user
from authentik.events.models import Notification


class TestFilter(TestCase):

    def test_filter(self):
        user = create_test_user()
        notif = Notification.objects.create(user=user)
        qs = apply_search(
            Notification.objects.all(), "user.id = $current_user", {"$current_user": user.pk}
        )
        self.assertEqual(qs.first(), notif)
