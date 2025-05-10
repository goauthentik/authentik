"""SCIM Errors"""

from authentik.common.exceptions import NotReportedException


class PatchError(NotReportedException):
    """Error raised within an atomic block when an error happened
    so nothing is saved"""
