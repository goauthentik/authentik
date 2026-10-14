"""User application pagination regressions and policy-filtering cost measurements."""

from statistics import median
from time import perf_counter
from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from authentik.core.api.applications import ApplicationViewSet
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_user
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.types import CACHE_PREFIX


class TestUserApplicationPagination(APITestCase):
    """Pages and totals must describe the target user's accessible applications."""

    def setUp(self):
        self.admin = create_test_admin_user()
        self.user = create_test_user()
        self.client.force_login(self.admin)
        self.url = reverse("authentik_api:application-accessible")
        self.apps = []
        # Denied applications before, between, and after allowed applications.
        for index in range(7):
            app = Application.objects.create(name=f"app-{index}", slug=f"app-{index}")
            PolicyBinding.objects.create(
                target=app, user=self.user if index % 2 else self.admin, order=0
            )
            self.apps.append(app)

    def test_pages(self):
        """Denied objects must not consume slots or inflate any pagination metadata."""
        for page, indices, expected_pagination in (
            (
                1,
                [1, 3],
                dict(
                    next=2,
                    previous=0,
                    count=3,
                    current=1,
                    total_pages=2,
                    start_index=1,
                    end_index=2,
                ),
            ),
            (
                2,
                [5],
                dict(
                    next=0,
                    previous=1,
                    count=3,
                    current=2,
                    total_pages=2,
                    start_index=3,
                    end_index=3,
                ),
            ),
        ):
            with self.subTest(page=page):
                response = self.client.get(
                    self.url, {"for_user": self.user.pk, "page_size": 2, "page": page}
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data["pagination"], expected_pagination)
                self.assertEqual(
                    [app["slug"] for app in response.data["results"]],
                    [self.apps[index].slug for index in indices],
                )
        response = self.client.get(self.url, {"for_user": self.user.pk, "page_size": 2, "page": 3})
        self.assertEqual(response.status_code, 404)

    def test_empty(self):
        """A user with no access gets an empty first page with a zero count."""
        response = self.client.get(self.url, {"for_user": create_test_user().pk, "page_size": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertEqual(
            response.data["pagination"],
            dict(next=0, previous=0, count=0, current=1, total_pages=1, start_index=0, end_index=0),
        )

    def test_filters_and_ordering(self):
        """Hidden objects and search filters are excluded; ordering survives policy filtering."""
        self.apps[3].meta_hide = True
        self.apps[3].save()
        response = self.client.get(
            self.url,
            {"for_user": self.user.pk, "page_size": 1, "ordering": "-name", "search": "app"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["count"], 2)
        self.assertEqual([app["slug"] for app in response.data["results"]], ["app-5"])
        response = self.client.get(self.url, {"for_user": self.user.pk, "search": "app-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["count"], 1)
        self.assertEqual([app["slug"] for app in response.data["results"]], ["app-1"])

    def test_expression_uses_target_user(self):
        """Dynamic policies also evaluate as the target user, including HTTP request context."""
        PolicyBinding.objects.all().delete()
        policy = ExpressionPolicy.objects.create(
            name="target-user",
            expression=(
                f"return request.user.pk == {self.user.pk} "
                f"and request.http_request.user.pk == {self.user.pk} "
                "and request.obj.slug in ('app-3', 'app-5')"
            ),
        )
        for app in self.apps:
            PolicyBinding.objects.create(target=app, policy=policy, order=0)
        response = self.client.get(self.url, {"for_user": self.user.pk, "page_size": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["pagination"]["count"], 2)
        self.assertEqual([app["slug"] for app in response.data["results"]], ["app-3", "app-5"])

    def test_invalid_target(self):
        """Malformed and nonexistent user IDs still fail validation."""
        for target in ("invalid", -1):
            with self.subTest(target=target):
                response = self.client.get(self.url, {"for_user": target})
                self.assertEqual(response.status_code, 400)

    def test_requires_user_applications_permission(self):
        """An unprivileged caller cannot list another user's applications."""
        self.client.force_login(self.user)
        response = self.client.get(self.url, {"for_user": self.admin.pk})
        self.assertEqual(response.status_code, 400)


class TestApplicationPaginationCost(APITestCase):
    """Compare the old and new filtering pipelines, excluding HTTP/authentication overhead.

    Measures real SQL, policy evaluation, and serialization with 10% accessible apps.
    Reports median elapsed time and query count over three runs, with cold and warm
    policy caches. Timings are informational; assertions cover policy execution
    counts and query budgets rather than machine-dependent deadlines. Run with --no-capture to see
    the table. These simple expressions do not model slow external policy calls.
    """

    def test_filtering_cost(self):
        """Expose full-set evaluation costs and guard against static-binding N+1 queries."""
        admin = create_test_admin_user()
        user = create_test_user()
        policy = ExpressionPolicy.objects.create(
            name="pagination-cost",
            expression="return int(request.obj.slug.split('-')[-1]) % 10 == 0",
        )
        apps = []
        print("\napps policy cache pipeline median_ms queries policy_executions")
        for size in (20, 140, 1000):
            for index in range(len(apps), size):
                apps.append(
                    Application.objects.create(name=f"app-{index:04d}", slug=f"app-{index:04d}")
                )
            for dynamic in (False, True):
                PolicyBinding.objects.filter(target__in=apps).delete()
                PolicyBinding.objects.bulk_create(
                    [
                        PolicyBinding(
                            target=app,
                            policy=policy if dynamic else None,
                            user=None if dynamic else (user if index % 10 == 0 else admin),
                            order=0,
                        )
                        for index, app in enumerate(apps)
                    ]
                )
                for warm in (False, True) if dynamic else (False,):
                    for full_set in (False, True):
                        durations, queries, executions = [], [], []
                        for _ in range(3):
                            cache.delete_many(cache.keys(f"{CACHE_PREFIX}*"))
                            if warm:
                                self._run_pipeline(admin, user, full_set)
                            with (
                                CaptureQueriesContext(connection) as captured,
                                patch.object(
                                    ExpressionPolicy,
                                    "passes",
                                    autospec=True,
                                    side_effect=ExpressionPolicy.passes,
                                ) as passes,
                            ):
                                start = perf_counter()
                                response = self._run_pipeline(admin, user, full_set)
                                durations.append((perf_counter() - start) * 1000)
                            queries.append(len(captured))
                            executions.append(passes.call_count)
                            evaluated = size if full_set else 20
                            self.assertEqual(
                                passes.call_count, evaluated if dynamic and not warm else 0
                            )
                            self.assertEqual(
                                len(response.data["results"]),
                                min(size // 10, 20) if full_set else 2,
                            )
                            self.assertEqual(
                                response.data["pagination"]["count"],
                                size // 10 if full_set else size,
                            )
                        print(
                            size,
                            "expression" if dynamic else "user-binding",
                            "warm" if warm else "cold",
                            "filter-first" if full_set else "page-first",
                            f"{median(durations):.2f}",
                            median(queries),
                            median(executions),
                        )
                        if not dynamic and full_set:
                            # Observed baseline: 18 queries. Allow small variations from
                            # cache state/setup, but keep the budget fixed as apps grow
                            # so per-application queries still fail this check.
                            self.assertLessEqual(
                                median(queries),
                                25,
                                f"Static bindings for {size} apps exceeded query budget: {queries}",
                            )

    def _run_pipeline(self, admin, user, full_set):
        """Reproduce each pipeline with fresh querysets and identical page size/serialization."""
        raw_request = APIRequestFactory().get("/", {"page_size": 20, "for_user": user.pk})
        force_authenticate(raw_request, user=admin)
        view = ApplicationViewSet(action="accessible", **ApplicationViewSet.accessible.kwargs)
        view.action_map = {"get": "accessible"}
        view.request = view.initialize_request(raw_request)
        view.format_kwarg = None
        queryset = view.filter_queryset(view.get_queryset()).exclude(meta_hide=True)
        if full_set:
            allowed = view._get_allowed_applications(queryset, user=user)
            page = view.paginator.paginate_queryset(allowed, view.request)
        else:
            candidates = view.paginator.paginate_queryset(queryset, view.request)
            page = view._get_allowed_applications(candidates, user=user)
        return view.get_paginated_response(view.get_serializer(page, many=True).data)
