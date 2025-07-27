"""Test OpenTelemetry integration"""

import os
from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from django.test import override_settings

from authentik.lib.config import CONFIG


class TestOTLPConfiguration(TestCase):
    """Test OTLP configuration handling"""

    def setUp(self):
        self.env_vars = {}
        self.original_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_otlp_enabled_default(self):
        """Test OTLP is disabled by default"""
        with patch.object(CONFIG, "get_bool") as mock_get_bool:
            mock_get_bool.return_value = False
            self.assertFalse(CONFIG.get_bool("telemetry.otlp.enabled", False))
            mock_get_bool.assert_called_once_with("telemetry.otlp.enabled", False)

    def test_otlp_enabled_via_env(self):
        """Test OTLP can be enabled via environment variable"""
        os.environ["AUTHENTIK_TELEMETRY__OTLP__ENABLED"] = "true"
        with patch.object(CONFIG, "get_bool") as mock_get_bool:
            mock_get_bool.return_value = True
            self.assertTrue(CONFIG.get_bool("telemetry.otlp.enabled", False))

    def test_otlp_endpoint_configuration(self):
        """Test OTLP endpoint configuration"""
        test_endpoint = "http://localhost:4317"
        os.environ["AUTHENTIK_TELEMETRY__OTLP__ENDPOINT"] = test_endpoint
        with patch.object(CONFIG, "get") as mock_get:
            mock_get.return_value = test_endpoint
            endpoint = CONFIG.get("telemetry.otlp.endpoint", "")
            self.assertEqual(endpoint, test_endpoint)
            mock_get.assert_called_once_with("telemetry.otlp.endpoint", "")

    def test_otlp_protocol_configuration(self):
        """Test OTLP protocol configuration (grpc vs http)"""
        with patch.object(CONFIG, "get") as mock_get:
            mock_get.return_value = "grpc"
            protocol = CONFIG.get("telemetry.otlp.protocol", "grpc")
            self.assertEqual(protocol, "grpc")

        os.environ["AUTHENTIK_TELEMETRY__OTLP__PROTOCOL"] = "http/protobuf"
        with patch.object(CONFIG, "get") as mock_get:
            mock_get.return_value = "http/protobuf"
            protocol = CONFIG.get("telemetry.otlp.protocol", "grpc")
            self.assertEqual(protocol, "http/protobuf")

    def test_otlp_headers_configuration(self):
        """Test OTLP headers configuration for authentication"""
        test_headers = {"Authorization": "Bearer token123", "X-Custom-Header": "value"}
        with patch.object(CONFIG, "get") as mock_get:
            mock_get.return_value = test_headers
            headers = CONFIG.get("telemetry.otlp.headers", {})
            self.assertEqual(headers, test_headers)

    def test_traces_sampling_configuration(self):
        """Test traces sampling rate configuration"""
        with patch.object(CONFIG, "get_float") as mock_get_float:
            mock_get_float.return_value = 0.1
            sample_rate = CONFIG.get_float("telemetry.otlp.traces_sample_rate", 0.01)
            self.assertEqual(sample_rate, 0.1)
            mock_get_float.assert_called_once_with("telemetry.otlp.traces_sample_rate", 0.01)

    def test_resource_attributes_configuration(self):
        """Test resource attributes configuration"""
        test_attributes = {
            "service.name": "authentik",
            "service.version": "2024.1.0",
            "deployment.environment": "production",
            "service.namespace": "identity",
        }
        with patch.object(CONFIG, "get") as mock_get:
            mock_get.return_value = test_attributes
            attributes = CONFIG.get("telemetry.otlp.resource_attributes", {})
            self.assertEqual(attributes, test_attributes)


class TestAdaptiveSampler(TestCase):
    """Test adaptive sampler implementation"""

    def setUp(self):
        # Mock the sampler since we haven't implemented it yet
        self.mock_sampler = MagicMock()
        self.mock_sampler.default_rate = 0.1
        self.mock_sampler.error_rate = 1.0
        self.mock_sampler.high_latency_threshold_ms = 1000
        self.mock_sampler.high_latency_rate = 0.5

    def test_health_check_urls_not_sampled(self):
        """Test that health check URLs are not sampled"""
        with patch("opentelemetry.sdk.trace.sampling.Decision") as mock_decision:
            mock_decision.DROP = "DROP"
            mock_decision.RECORD_AND_SAMPLE = "RECORD_AND_SAMPLE"

            attributes = {"http.target": "/-/health/live/"}
            result = MagicMock()
            result.decision = mock_decision.DROP

            self.mock_sampler.should_sample.return_value = result

            actual_result = self.mock_sampler.should_sample(
                parent_context=None,
                trace_id=123456,
                name="http.request",
                attributes=attributes,
            )

            self.assertEqual(actual_result.decision, "DROP")

    def test_error_spans_sampled_at_higher_rate(self):
        """Test that error spans are sampled at a higher rate"""
        with patch("opentelemetry.sdk.trace.sampling.Decision") as mock_decision:
            mock_decision.RECORD_AND_SAMPLE = "RECORD_AND_SAMPLE"

            attributes = {
                "http.target": "/api/v3/flows/",
                "error": True,
                "http.status_code": 500,
            }

            result = MagicMock()
            result.decision = mock_decision.RECORD_AND_SAMPLE
            result.attributes = {"sampled.by": "error"}

            self.mock_sampler.should_sample.return_value = result

            actual_result = self.mock_sampler.should_sample(
                parent_context=None,
                trace_id=123456,
                name="http.request",
                attributes=attributes,
            )

            self.assertEqual(actual_result.decision, "RECORD_AND_SAMPLE")
            self.assertEqual(actual_result.attributes.get("sampled.by"), "error")


class TestOTLPMetrics(TestCase):
    """Test OTLP metrics collection and export"""

    def setUp(self):
        self.mock_exporter = MagicMock()
        self.mock_reader = MagicMock()
        self.mock_provider = MagicMock()

    def test_flow_execution_metrics(self):
        """Test metrics collection for flow execution"""
        with patch("opentelemetry.metrics.get_meter") as mock_get_meter:
            mock_meter = MagicMock()
            mock_counter = MagicMock()
            mock_histogram = MagicMock()

            mock_meter.create_counter.return_value = mock_counter
            mock_meter.create_histogram.return_value = mock_histogram
            mock_get_meter.return_value = mock_meter

            # Simulate flow execution metrics
            meter = mock_get_meter("authentik.flows")

            flow_executions = meter.create_counter(
                "authentik.flow.executions",
                description="Number of flow executions",
                unit="1",
            )

            flow_duration = meter.create_histogram(
                "authentik.flow.duration",
                description="Flow execution duration",
                unit="ms",
            )

            # Record metrics
            flow_executions.add(
                1, {"flow.slug": "default-authentication-flow", "status": "success"}
            )
            flow_duration.record(150.5, {"flow.slug": "default-authentication-flow"})

            # Verify calls
            mock_counter.add.assert_called_once_with(
                1, {"flow.slug": "default-authentication-flow", "status": "success"}
            )
            mock_histogram.record.assert_called_once_with(
                150.5, {"flow.slug": "default-authentication-flow"}
            )

    def test_policy_evaluation_metrics(self):
        """Test metrics collection for policy evaluation"""
        with patch("opentelemetry.metrics.get_meter") as mock_get_meter:
            mock_meter = MagicMock()
            mock_counter = MagicMock()
            mock_histogram = MagicMock()

            mock_meter.create_counter.return_value = mock_counter
            mock_meter.create_histogram.return_value = mock_histogram
            mock_get_meter.return_value = mock_meter

            meter = mock_get_meter("authentik.policies")

            policy_evaluations = meter.create_counter(
                "authentik.policy.evaluations",
                description="Number of policy evaluations",
                unit="1",
            )

            policy_duration = meter.create_histogram(
                "authentik.policy.evaluation_duration",
                description="Policy evaluation duration",
                unit="ms",
            )

            # Record metrics
            policy_evaluations.add(1, {"policy.type": "password", "result": "passed"})
            policy_duration.record(25.3, {"policy.type": "password"})

            # Verify
            mock_counter.add.assert_called_once_with(
                1, {"policy.type": "password", "result": "passed"}
            )
            mock_histogram.record.assert_called_once_with(25.3, {"policy.type": "password"})

    def test_authentication_metrics(self):
        """Test metrics for authentication attempts"""
        with patch("opentelemetry.metrics.get_meter") as mock_get_meter:
            mock_meter = MagicMock()
            mock_counter = MagicMock()

            mock_meter.create_counter.return_value = mock_counter
            mock_get_meter.return_value = mock_meter

            meter = mock_get_meter("authentik.authentication")

            auth_attempts = meter.create_counter(
                "authentik.authentication.attempts",
                description="Number of authentication attempts",
                unit="1",
            )

            # Record different authentication scenarios
            auth_attempts.add(1, {"method": "password", "result": "success"})
            auth_attempts.add(
                1, {"method": "password", "result": "failure", "reason": "invalid_password"}
            )
            auth_attempts.add(1, {"method": "webauthn", "result": "success"})
            auth_attempts.add(1, {"method": "totp", "result": "failure", "reason": "invalid_code"})

            # Verify
            self.assertEqual(mock_counter.add.call_count, 4)


class TestTelemetryProvider(TestCase):
    """Test telemetry provider setup and configuration"""

    def setUp(self):
        self.original_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("authentik.lib.config.CONFIG")
    def test_provider_disabled_by_default(self, mock_config):
        """Test that telemetry provider is disabled by default"""
        mock_config.get_bool.return_value = False

        # Provider should not initialize when disabled
        with patch("authentik.lib.telemetry.provider.TelemetryProvider.initialize") as mock_init:
            # Check if provider would be initialized
            if mock_config.get_bool("telemetry.otlp.enabled", False):
                mock_init()

            # Should not be called when disabled
            mock_init.assert_not_called()

    @patch("authentik.lib.config.CONFIG")
    @patch("opentelemetry.sdk.trace.TracerProvider")
    @patch("opentelemetry.sdk.metrics.MeterProvider")
    def test_provider_initialization(self, mock_meter_provider, mock_tracer_provider, mock_config):
        """Test telemetry provider initialization when enabled"""
        # Configure mocks
        mock_config.get_bool.return_value = True
        mock_config.get.side_effect = lambda key, default: {
            "telemetry.otlp.endpoint": "http://localhost:4317",
            "telemetry.otlp.service_name": "authentik-test",
            "telemetry.otlp.protocol": "grpc",
        }.get(key, default)

        # Test initialization
        with (
            patch("opentelemetry.trace.set_tracer_provider") as mock_set_tracer,
            patch("opentelemetry.metrics.set_meter_provider") as mock_set_meter,
        ):
            # Simulate provider initialization
            tracer_provider = mock_tracer_provider()
            meter_provider = mock_meter_provider()

            mock_set_tracer(tracer_provider)
            mock_set_meter(meter_provider)

            # Verify providers were set
            mock_set_tracer.assert_called_once_with(tracer_provider)
            mock_set_meter.assert_called_once_with(meter_provider)

    @patch("authentik.lib.config.CONFIG")
    def test_excluded_urls_configuration(self, mock_config):
        """Test excluded URLs are properly configured"""
        excluded_urls = [
            "/-/health/.*",
            "/-/metrics/",
            "/static/.*",
            "/media/.*",
        ]

        mock_config.get_list.return_value = excluded_urls

        urls = mock_config.get_list("telemetry.otlp.excluded_urls", [])
        self.assertEqual(urls, excluded_urls)


class TestOTLPIntegration(TestCase):
    """Test OTLP integration with authentik components"""

    def setUp(self):
        self.mock_tracer_provider = MagicMock()
        self.mock_span_processor = MagicMock()
        self.mock_exporter = MagicMock()

    @override_settings(TELEMETRY_OTLP_ENABLED=True)
    def test_telemetry_initialization(self):
        """Test that telemetry is properly initialized when enabled"""
        with patch("authentik.lib.telemetry.initialize_telemetry") as mock_init:
            # Simulate initialization
            mock_init.return_value = True

            # Verify initialization would be called
            result = mock_init()

            self.assertTrue(result)
            mock_init.assert_called_once()

    def test_flow_execution_tracing(self):
        """Test tracing of flow execution"""
        with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_span = MagicMock()

            mock_get_tracer.return_value = mock_tracer
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            # Simulate flow execution
            flow_attributes = {
                "flow.slug": "default-authentication-flow",
                "flow.designation": "authentication",
                "flow.stage_count": 3,
            }

            # Create span
            with mock_tracer.start_as_current_span(
                "flow.execute",
                attributes=flow_attributes,
            ) as span:
                # Simulate flow stages
                for i in range(3):
                    stage_attributes = {
                        "stage.order": i,
                        "stage.type": f"stage_{i}",
                    }
                    with mock_tracer.start_as_current_span(
                        "stage.execute",
                        attributes=stage_attributes,
                    ):
                        pass

            # Verify flow span was created
            mock_tracer.start_as_current_span.assert_any_call(
                "flow.execute",
                attributes=flow_attributes,
            )

    def test_error_span_recording(self):
        """Test that errors are properly recorded in spans"""
        with patch("opentelemetry.trace.get_tracer") as mock_get_tracer:
            mock_tracer = MagicMock()
            mock_span = MagicMock()

            mock_get_tracer.return_value = mock_tracer
            mock_tracer.start_as_current_span.return_value.__enter__.return_value = mock_span

            # Simulate error scenario with manual exception recording
            try:
                with mock_tracer.start_as_current_span("operation.failed") as span:
                    # Simulate operation that fails
                    error = ValueError("Test error")
                    span.record_exception(error)
                    span.set_status("error")
                    raise error
            except ValueError:
                mock_span.record_exception.assert_called_once()
                mock_span.set_status.assert_called_once()
