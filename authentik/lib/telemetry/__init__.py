"""OpenTelemetry integration for authentik"""

from authentik.lib.telemetry.provider import TelemetryProvider

# Global telemetry provider instance
provider = TelemetryProvider()


def initialize_telemetry():
    """Initialize OpenTelemetry telemetry with OTLP configuration"""
    return provider.initialize()


def get_tracer(name: str = "authentik"):
    """Get a tracer instance"""
    return provider.get_tracer(name)


def get_meter(name: str = "authentik"):
    """Get a meter instance"""
    return provider.get_meter(name)


def record_flow_execution(flow_name: str, duration: float, success: bool):
    """Record flow execution metrics"""
    provider.record_flow_execution(flow_name, duration, success)


def record_policy_evaluation(policy_name: str, duration: float, result: bool):
    """Record policy evaluation metrics"""
    provider.record_policy_evaluation(policy_name, duration, result)


def record_authentication(method: str, success: bool, duration: float):
    """Record authentication metrics"""
    provider.record_authentication(method, success, duration)
