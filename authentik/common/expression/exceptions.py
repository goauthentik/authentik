from authentik.common.exceptions import NotReportedException


class ControlFlowException(NotReportedException):
    """Exceptions used to control the flow from exceptions, not reported as a warning/
    error in logs"""
