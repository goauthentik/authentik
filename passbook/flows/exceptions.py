"""flow exceptions"""


class FlowNonApplicableException(BaseException):
    """Exception raised when a Flow does not apply to a user."""


class EmptyFlowException(BaseException):
    """Exception raised when a Flow Plan is empty"""
