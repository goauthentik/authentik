from django.db.models import OrderBy
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from authentik.api.ordering import NullsAwareOrderingFilter
from authentik.core.models import Token, User


class MockView:
    ordering_fields = "__all__"
    ordering = None


class TestNullsAwareOrderingFilter(TestCase):

    def setUp(self):
        self.filter = NullsAwareOrderingFilter()
        self.view = MockView()
        factory = APIRequestFactory()
        self._req = lambda ordering: Request(factory.get("/", {"ordering": ordering}))

    def _order_by(self, model, ordering):
        qs = model.objects.all()
        return self.filter.filter_queryset(self._req(ordering), qs, self.view).query.order_by

    def test_nullable_asc_nulls_first(self):
        """Ascending sort on a nullable field rewrites to nulls_first=True."""
        (expr,) = self._order_by(User, "last_login")
        self.assertIsInstance(expr, OrderBy)
        self.assertFalse(expr.descending)
        self.assertTrue(expr.nulls_first)

    def test_nullable_desc_nulls_last(self):
        """Descending sort on a nullable field rewrites to nulls_last=True."""
        (expr,) = self._order_by(User, "-last_login")
        self.assertIsInstance(expr, OrderBy)
        self.assertTrue(expr.descending)
        self.assertTrue(expr.nulls_last)

    def test_non_nullable_passes_through(self):
        """Non-nullable fields are left as plain string terms."""
        (expr,) = self._order_by(User, "username")
        self.assertEqual(expr, "username")

    def test_mixed_ordering(self):
        """Only nullable terms are rewritten; non-nullable terms pass through unchanged."""
        first, second = self._order_by(User, "username,-last_login")
        self.assertEqual(first, "username")
        self.assertIsInstance(second, OrderBy)
        self.assertTrue(second.descending)
        self.assertTrue(second.nulls_last)

    def test_expires_nullable(self):
        """expires on ExpiringModel is nullable and is rewritten correctly."""
        (expr,) = self._order_by(Token, "-expires")
        self.assertIsInstance(expr, OrderBy)
        self.assertTrue(expr.descending)
        self.assertTrue(expr.nulls_last)
