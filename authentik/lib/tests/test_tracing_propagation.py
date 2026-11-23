"""Trace context propagation across service-mesh header formats"""

from django.test import SimpleTestCase
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import get_current_span

from authentik.lib.tracing.otel import OpenTelemetryTracer

TRACE_ID = "80f198ee56343ba864fe8b2a57d3eff7"


class TestTracingPropagation(SimpleTestCase):
    """Verify both W3C and B3 (Istio/Envoy) headers are extracted and injected"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        OpenTelemetryTracer().setup_pre_fork()

    def test_extract_b3_multi(self):
        """Istio's default: x-b3-* multi headers"""
        ctx = extract(
            {
                "x-b3-traceid": TRACE_ID,
                "x-b3-spanid": "e457b5a2e4d86bd1",
                "x-b3-sampled": "1",
            }
        )
        self.assertEqual(
            format(get_current_span(ctx).get_span_context().trace_id, "032x"), TRACE_ID
        )

    def test_extract_w3c(self):
        """Non-mesh callers still work"""
        ctx = extract({"traceparent": f"00-{TRACE_ID}-e457b5a2e4d86bd1-01"})
        self.assertEqual(
            format(get_current_span(ctx).get_span_context().trace_id, "032x"), TRACE_ID
        )

    def test_inject_both_formats(self):
        """Outbound requests carry both, so the next sidecar links up either way"""
        ctx = extract({"traceparent": f"00-{TRACE_ID}-e457b5a2e4d86bd1-01"})
        carrier = {}
        inject(carrier, context=ctx)
        self.assertIn("traceparent", carrier)
        self.assertEqual(carrier["x-b3-traceid"], TRACE_ID)
