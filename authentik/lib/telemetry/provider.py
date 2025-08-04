"""OpenTelemetry provider implementation"""

import logging
import re

from authentik.lib.config import CONFIG

logger = logging.getLogger(__name__)

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter as HTTPMetricExporter,
    )
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as HTTPSpanExporter,
    )
    from opentelemetry.instrumentation.django import DjangoInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    logger.warning("OpenTelemetry packages not available. Telemetry disabled.")
    OPENTELEMETRY_AVAILABLE = False

    # Mock classes for when OpenTelemetry is not available
    class TracerProvider:
        def get_tracer(self, *args, **kwargs):
            return NoOpTracer()

    class MeterProvider:
        def get_meter(self, *args, **kwargs):
            return NoOpMeter()

    class NoOpTracer:
        def start_as_current_span(self, *args, **kwargs):
            return NoOpSpan()

        def start_span(self, *args, **kwargs):
            return NoOpSpan()

    class NoOpMeter:
        def create_counter(self, *args, **kwargs):
            return NoOpCounter()

        def create_histogram(self, *args, **kwargs):
            return NoOpHistogram()

    class NoOpSpan:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def set_attribute(self, *args, **kwargs):
            pass

        def set_status(self, *args, **kwargs):
            pass

        def record_exception(self, *args, **kwargs):
            pass

    class NoOpCounter:
        def add(self, *args, **kwargs):
            pass

    class NoOpHistogram:
        def record(self, *args, **kwargs):
            pass


class AdaptiveSampler:
    """Custom sampler that excludes health checks and samples errors at higher rates"""

    def __init__(self, default_rate: float = 0.01, error_rate: float = 1.0):
        self.default_rate = default_rate
        self.error_rate = error_rate
        self.health_check_patterns = [
            re.compile(r"/health/?$"),
            re.compile(r"/metrics/?$"),
            re.compile(r"/readiness/?$"),
            re.compile(r"/liveness/?$"),
        ]

    def should_sample(self, url_path: str, is_error: bool = False) -> bool:
        """Determine if a request should be sampled"""
        # Never sample health check endpoints
        for pattern in self.health_check_patterns:
            if pattern.search(url_path):
                return False

        # Sample errors at higher rate
        if is_error:
            return True  # Always sample errors for now, could use error_rate

        # Default sampling logic would go here
        # For now, return True to sample everything except health checks
        return True


class TelemetryProvider:
    """Central provider for OpenTelemetry telemetry configuration"""

    def __init__(self):
        self._initialized = False
        self._tracer_provider: TracerProvider | None = None
        self._meter_provider: MeterProvider | None = None
        self._tracer = None
        self._meter = None
        self._sampler = AdaptiveSampler()

        # Metrics
        self._flow_duration_histogram = None
        self._policy_duration_histogram = None
        self._auth_counter = None
        self._flow_counter = None
        self._policy_counter = None

    def is_enabled(self) -> bool:
        """Check if telemetry is enabled"""
        return CONFIG.get_bool("telemetry.otlp.enabled", False)

    def initialize(self) -> bool:
        """Initialize OpenTelemetry with OTLP configuration"""
        if self._initialized:
            return True

        if not self.is_enabled():
            logger.debug("OTLP telemetry disabled")
            return False

        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry packages not available")
            return False

        try:
            # Configure resource attributes
            resource_attributes = self._get_resource_attributes()
            resource = Resource.create(resource_attributes)

            # Initialize tracing
            self._setup_tracing(resource)

            # Initialize metrics
            self._setup_metrics(resource)

            # Initialize instrumentations
            self._setup_instrumentations()

            self._initialized = True
            logger.info("OpenTelemetry telemetry initialized successfully")
            return True

        except Exception as exc:
            logger.error("Failed to initialize OpenTelemetry telemetry", exc_info=exc)
            return False

    def _get_resource_attributes(self) -> dict:
        """Get resource attributes from configuration"""
        attributes = {
            SERVICE_NAME: CONFIG.get("telemetry.otlp.service_name", "authentik"),
            SERVICE_VERSION: CONFIG.get("telemetry.otlp.service_version", "unknown"),
        }

        # Add custom resource attributes
        custom_attrs = CONFIG.get("telemetry.otlp.resource_attributes", {})
        if isinstance(custom_attrs, dict):
            attributes.update(custom_attrs)

        return attributes

    def _setup_tracing(self, resource: "Resource"):
        """Setup tracing configuration"""
        self._tracer_provider = TracerProvider(resource=resource)

        # Configure OTLP exporter
        endpoint = CONFIG.get("telemetry.otlp.endpoint", "")
        protocol = CONFIG.get("telemetry.otlp.protocol", "grpc")
        headers = CONFIG.get("telemetry.otlp.headers", {})

        if endpoint:
            if protocol.lower() == "http":
                span_exporter = HTTPSpanExporter(
                    endpoint=f"{endpoint}/v1/traces",
                    headers=headers,
                )
            else:  # Default to gRPC
                span_exporter = OTLPSpanExporter(
                    endpoint=endpoint,
                    headers=headers,
                )

            span_processor = BatchSpanProcessor(span_exporter)
            self._tracer_provider.add_span_processor(span_processor)

        # Set global tracer provider
        trace.set_tracer_provider(self._tracer_provider)
        self._tracer = self._tracer_provider.get_tracer("authentik")

    def _setup_metrics(self, resource: "Resource"):
        """Setup metrics configuration"""
        endpoint = CONFIG.get("telemetry.otlp.endpoint", "")
        protocol = CONFIG.get("telemetry.otlp.protocol", "grpc")
        headers = CONFIG.get("telemetry.otlp.headers", {})

        if endpoint:
            if protocol.lower() == "http":
                metric_exporter = HTTPMetricExporter(
                    endpoint=f"{endpoint}/v1/metrics",
                    headers=headers,
                )
            else:  # Default to gRPC
                metric_exporter = OTLPMetricExporter(
                    endpoint=endpoint,
                    headers=headers,
                )

            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=60000,  # 1 minute
            )

            self._meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
        else:
            self._meter_provider = MeterProvider(resource=resource)

        # Set global meter provider
        metrics.set_meter_provider(self._meter_provider)
        self._meter = self._meter_provider.get_meter("authentik")

        # Create metrics
        self._create_metrics()

    def _create_metrics(self):
        """Create application metrics"""
        if not self._meter:
            return

        self._flow_duration_histogram = self._meter.create_histogram(
            name="authentik_flow_execution_duration_seconds",
            description="Duration of flow executions",
            unit="s",
        )

        self._policy_duration_histogram = self._meter.create_histogram(
            name="authentik_policy_evaluation_duration_seconds",
            description="Duration of policy evaluations",
            unit="s",
        )

        self._auth_counter = self._meter.create_counter(
            name="authentik_authentication_total",
            description="Total number of authentication attempts",
        )

        self._flow_counter = self._meter.create_counter(
            name="authentik_flow_execution_total", description="Total number of flow executions"
        )

        self._policy_counter = self._meter.create_counter(
            name="authentik_policy_evaluation_total",
            description="Total number of policy evaluations",
        )

    def _setup_instrumentations(self):
        """Setup automatic instrumentations"""
        try:
            # Instrument Django
            DjangoInstrumentor().instrument()

            # Instrument requests
            RequestsInstrumentor().instrument()

            # Instrument PostgreSQL
            Psycopg2Instrumentor().instrument()

            # Instrument Redis
            RedisInstrumentor().instrument()

            logger.debug("OpenTelemetry instrumentations initialized")
        except Exception as exc:
            logger.warning("Failed to initialize some instrumentations", exc_info=exc)

    def get_tracer(self, name: str = "authentik"):
        """Get a tracer instance"""
        if self._tracer_provider:
            return self._tracer_provider.get_tracer(name)
        return None

    def get_meter(self, name: str = "authentik"):
        """Get a meter instance"""
        if self._meter_provider:
            return self._meter_provider.get_meter(name)
        return None

    def record_flow_execution(self, flow_name: str, duration: float, success: bool):
        """Record flow execution metrics"""
        if not self._flow_duration_histogram or not self._flow_counter:
            return

        attributes = {
            "flow_name": flow_name,
            "success": success,
        }

        self._flow_duration_histogram.record(duration, attributes)
        self._flow_counter.add(1, attributes)

    def record_policy_evaluation(self, policy_name: str, duration: float, result: bool):
        """Record policy evaluation metrics"""
        if not self._policy_duration_histogram or not self._policy_counter:
            return

        attributes = {
            "policy_name": policy_name,
            "result": result,
        }

        self._policy_duration_histogram.record(duration, attributes)
        self._policy_counter.add(1, attributes)

    def record_authentication(self, method: str, success: bool, duration: float):
        """Record authentication metrics"""
        if not self._auth_counter:
            return

        attributes = {
            "method": method,
            "success": success,
        }

        self._auth_counter.add(1, attributes)
