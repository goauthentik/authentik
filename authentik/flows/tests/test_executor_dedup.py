"""flow executor duplicate-submission deduplication tests"""

from threading import Event as ThreadEvent
from threading import Thread
from time import monotonic
from unittest.mock import patch

from django.conf import settings
from django.db import connection
from django.http import HttpResponseRedirect
from django.test import Client, TransactionTestCase
from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.stages.dummy.models import DummyStage


class TestFlowExecutorDedup(FlowTestCase):
    """Test deduplication of identical concurrent submissions"""

    def setUp(self):
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        for order in range(2):
            FlowStageBinding.objects.create(
                target=self.flow,
                stage=DummyStage.objects.create(name=generate_id()),
                order=order,
            )
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def _patch_solve(self, **kwargs):
        """Patch _solve_challenge with a call-counting mock"""
        if "side_effect" not in kwargs:
            kwargs["side_effect"] = FlowExecutorView._solve_challenge
        return patch.object(FlowExecutorView, "_solve_challenge", autospec=True, **kwargs)

    def test_identical_submission_replayed(self):
        """A duplicate of a submission to the same stage replays its redirect and cookies"""

        def solve(view, request, *args, **kwargs):
            # Redirect without advancing the plan, as a concurrent duplicate would see it
            response = HttpResponseRedirect(self.url)
            response.set_cookie("marker", "value")
            return response

        self.client.get(self.url)
        with self._patch_solve(side_effect=solve) as mock:
            first = self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
            second = self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(second.status_code, first.status_code)
        self.assertEqual(second.headers["Location"], first.headers["Location"])
        self.assertEqual(second.cookies["marker"].value, "value")
        self.assertIn(settings.SESSION_COOKIE_NAME, second.cookies)

    def test_identical_body_across_stages_not_deduplicated(self):
        """Identical bodies submitted to consecutive stages are distinct submissions"""
        self.client.get(self.url)
        with self._patch_solve() as solve:
            first = self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
            second = self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
        self.assertEqual(solve.call_count, 2)
        self.assertEqual(first.status_code, 302)
        # The second stage finishes the flow instead of replaying the first redirect
        self.assertEqual(second.status_code, 200)
        self.assertIsNone(self.get_flow_plan())

    def test_different_submissions_not_deduplicated(self):
        """Distinct submissions in the same session are both processed"""
        self.client.get(self.url)
        with self._patch_solve() as solve:
            self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
            self.client.post(
                self.url,
                {"component": "ak-stage-dummy", "marker": generate_id()},
                content_type="application/json",
            )
        self.assertEqual(solve.call_count, 2)

    def test_no_session_fails_open(self):
        """A submission without an established session is processed normally"""
        with self._patch_solve() as solve:
            response = self.client.post(
                self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
            )
        self.assertEqual(solve.call_count, 1)
        self.assertEqual(response.status_code, 302)


class TestFlowExecutorDedupConcurrent(TransactionTestCase):
    """Test deduplication of truly concurrent submissions"""

    def setUp(self):
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        for order in range(2):
            FlowStageBinding.objects.create(
                target=self.flow,
                stage=DummyStage.objects.create(name=generate_id()),
                order=order,
            )
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def _waiting_advisory_locks(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted"
            )
            return cursor.fetchone()[0]

    def test_concurrent_duplicate_waits_and_replays(self):
        """A duplicate arriving mid-submission waits for the first and replays its redirect"""
        self.client.get(self.url)
        duplicate_client = Client()
        duplicate_client.cookies = self.client.cookies

        entered = ThreadEvent()
        release = ThreadEvent()
        responses = {}
        errors = []
        real_solve = FlowExecutorView._solve_challenge

        def solve(view, request, *args, **kwargs):
            entered.set()
            if not release.wait(timeout=10):
                errors.append("first submission was never released")
            return real_solve(view, request, *args, **kwargs)

        def submit(name: str, client: Client):
            try:
                responses[name] = client.post(
                    self.url, {"component": "ak-stage-dummy"}, content_type="application/json"
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)
            finally:
                connection.close()

        with patch.object(
            FlowExecutorView, "_solve_challenge", autospec=True, side_effect=solve
        ) as mock:
            first = Thread(target=submit, args=("first", self.client))
            first.start()
            self.assertTrue(entered.wait(timeout=10), "first submission never reached the stage")
            duplicate = Thread(target=submit, args=("duplicate", duplicate_client))
            duplicate.start()
            deadline = monotonic() + 10
            while self._waiting_advisory_locks() < 1:
                self.assertLess(monotonic(), deadline, "duplicate never waited on the lock")
            release.set()
            first.join(timeout=15)
            duplicate.join(timeout=15)

        self.assertEqual(errors, [])
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(responses["first"].status_code, 302)
        self.assertEqual(responses["duplicate"].status_code, 302)
        self.assertEqual(
            responses["duplicate"].headers["Location"], responses["first"].headers["Location"]
        )
        self.assertIn(settings.SESSION_COOKIE_NAME, responses["duplicate"].cookies)
