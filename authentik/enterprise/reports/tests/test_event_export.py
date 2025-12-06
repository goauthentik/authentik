from django.contrib.contenttypes.models import ContentType
from django.test.testcases import TestCase

from authentik.core.tests.utils import create_test_user
from authentik.enterprise.reports.models import DataExport
from authentik.enterprise.reports.tests.utils import _add_perm, patch_license


@patch_license
class TestEventExport(TestCase):
    def setUp(self) -> None:
        self.user = create_test_user()
        _add_perm(self.user, "view_event", "authentik_events")
        from authentik.events.models import Event, EventAction

        self.e1 = Event.new(EventAction.LOGIN, user=self.user)
        self.e1.save()
        self.e2 = Event.new(EventAction.LOGIN_FAILED, user=self.user)
        self.e2.save()

    def test_type_filter(self):
        from authentik.events.models import Event, EventAction

        export = DataExport.objects.create(
            content_type=ContentType.objects.get_for_model(Event),
            requested_by=self.user,
            query_params={"actions": [EventAction.LOGIN]},
        )
        records = list(export.get_queryset())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.e1)
