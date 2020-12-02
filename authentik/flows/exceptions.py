"""flow exceptions"""


class FlowNonApplicableException(BaseException):
    """Flow does not apply to current user (denied by policy)."""


class EmptyFlowException(BaseException):
    """Flow has no stages."""
