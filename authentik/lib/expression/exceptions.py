from authentik.lib.sentry import SentryIgnoredException


class ControlFlowException(SentryIgnoredException):
    """Exceptions used to control the flow from exceptions, not reported as a warning/
    error in logs"""
