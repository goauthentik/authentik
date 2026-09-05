"""Attribute filtering must not load all matches before pagination."""

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.core.api.groups import GroupFilter
from authentik.core.api.users import UsersFilter
from authentik.core.models import Group, User
from authentik.core.tests.utils import create_test_user
from authentik.lib.generators import generate_id


class TestAttributeFilters(TestCase):
    """Check filtering without materializing matching objects or their relations."""

    def test_filter_before_pagination(self):
        user = create_test_user(attributes={"department": "engineering"})
        group = Group.objects.create(name=generate_id(), attributes={"department": "engineering"})
        group.users.add(user)
        for filter_class, model, relation, expected in (
            (UsersFilter, User, "groups", user),
            (GroupFilter, Group, "users", group),
        ):
            with self.subTest(model=model):
                queryset = model.objects.filter(pk=expected.pk).prefetch_related(relation)
                for department, matches in (("engineering", [expected]), ("sales", [])):
                    with self.subTest(department=department):
                        with self.assertNumQueries(1):
                            filtered = filter_class().filter_attributes(
                                queryset, "attributes", f'{{"department": "{department}"}}'
                            )
                        self.assertEqual(list(filtered), matches)

    def test_invalid_json(self):
        for filter_class in (UsersFilter, GroupFilter):
            for value in ('{"department":', "[]", "null"):
                with self.subTest(filter=filter_class, value=value):
                    with self.assertNumQueries(0), self.assertRaises(ValidationError):
                        filter_class().filter_attributes(None, "attributes", value)

    def test_invalid_lookup_returns_original_queryset(self):
        for filter_class, model in ((UsersFilter, User), (GroupFilter, Group)):
            with self.subTest(model=model):
                queryset = model.objects.all()
                with self.assertNumQueries(0):
                    filtered = filter_class().filter_attributes(
                        queryset, "attributes", '{"department__isnull": "invalid"}'
                    )
                self.assertIs(filtered, queryset)
