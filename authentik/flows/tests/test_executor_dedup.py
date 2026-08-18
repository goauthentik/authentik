"""flow executor duplicate-submission deduplication tests"""

from itertools import count
from unittest.mock import patch

from django.core.cache import cache
from django.http import StreamingHttpResponse
from django.template.response import SimpleTemplateResponse
from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import CACHE_DEDUP_PREFIX, FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.stages.dummy.models import DummyStage
from authentik.stages.identification.models import IdentificationStage, UserFields


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

    def _patch_solve(self):
        """Patch _solve_challenge with a call-counting passthrough"""
        return patch.object(
            FlowExecutorView,
            "_solve_challenge",
            autospec=True,
            side_effect=FlowExecutorView._solve_challenge,
        )

    def test_identical_submission_replayed(self):
        """An identical duplicate submission to the same stage is replayed, not
        processed again"""
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        FlowStageBinding.objects.create(
            target=flow,
            stage=IdentificationStage.objects.create(
                name=generate_id(),
                user_fields=[UserFields.USERNAME],
                pretend_user_exists=False,
            ),
            order=0,
        )
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        body = {"component": "ak-stage-identification", "uid_field": "does-not-exist"}
        self.client.get(url)
        with self._patch_solve() as solve:
            first = self.client.post(url, body)
            second = self.client.post(url, body)
        self.assertEqual(solve.call_count, 1)
        self.assertEqual(second.status_code, first.status_code)
        self.assertEqual(second.content, first.content)

    def test_identical_body_across_stages_not_deduplicated(self):
        """Identical bodies submitted to consecutive stages are distinct submissions"""
        self.client.get(self.url)
        with self._patch_solve() as solve:
            first = self.client.post(self.url, {"component": "ak-stage-dummy"})
            second = self.client.post(self.url, {"component": "ak-stage-dummy"})
        self.assertEqual(solve.call_count, 2)
        self.assertEqual(first.status_code, 302)
        # The second submission was processed by the second stage, finishing the
        # flow, instead of receiving a replay of the first stage's 302
        self.assertEqual(second.status_code, 200)
        self.assertIsNone(self.get_flow_plan())

    def test_different_submissions_not_deduplicated(self):
        """Distinct submissions in the same session are both processed"""
        self.client.get(self.url)
        with self._patch_solve() as solve:
            self.client.post(self.url, {"component": "ak-stage-dummy"})
            self.client.post(self.url, {"component": "ak-stage-dummy", "marker": generate_id()})
        self.assertEqual(solve.call_count, 2)

    def test_waiting_duplicate_replays_stored_response(self):
        """A duplicate that loses the lock waits for and replays the winner's response"""
        self.client.get(self.url)
        stored = {
            "status": 302,
            "content": b"",
            "content_type": "text/html; charset=utf-8",
            "location": self.url,
        }
        real_get = cache.get
        real_add = cache.add
        dedup_gets = count()
        # Miss on the pre-lock check and the first poll, then hit
        misses_before_hit = 2

        def dedup_get(key, *args, **kwargs):
            if isinstance(key, str) and key.startswith(CACHE_DEDUP_PREFIX):
                return stored if next(dedup_gets) >= misses_before_hit else None
            return real_get(key, *args, **kwargs)

        def dedup_add(key, *args, **kwargs):
            if isinstance(key, str) and key.startswith(CACHE_DEDUP_PREFIX):
                return False
            return real_add(key, *args, **kwargs)

        with (
            self._patch_solve() as solve,
            patch("authentik.flows.views.executor.cache.get", side_effect=dedup_get),
            patch("authentik.flows.views.executor.cache.add", side_effect=dedup_add),
        ):
            response = self.client.post(self.url, {"component": "ak-stage-dummy"})
        self.assertEqual(solve.call_count, 0)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers.get("Location"), self.url)

    def test_no_session_fails_open(self):
        """A submission without an established session is processed normally"""
        with self._patch_solve() as solve:
            response = self.client.post(self.url, {"component": "ak-stage-dummy"})
        self.assertEqual(solve.call_count, 1)
        self.assertEqual(response.status_code, 302)

    def test_unreplayable_responses_not_stored(self):
        """Streaming and unrendered responses are never stored for replay"""
        self.assertIsNone(
            FlowExecutorView._dedup_serialize_response(StreamingHttpResponse(iter([b""])))
        )
        self.assertIsNone(
            FlowExecutorView._dedup_serialize_response(SimpleTemplateResponse("dummy.html"))
        )
