from authentik.lib.tracing.exceptions import TracingIgnoredException


class ControlFlowException(TracingIgnoredException):
    """Exceptions used to control the flow from exceptions, not reported as a warning/
    error in logs"""
