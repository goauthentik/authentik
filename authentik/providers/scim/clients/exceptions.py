"""SCIM Client exceptions"""

from pydantic import ValidationError
from requests import Response

from authentik.common.scim.schema import SCIMError
from authentik.lib.sync.outgoing.exceptions import TransientSyncException


class SCIMRequestException(TransientSyncException):
    """Exception raised when an SCIM request fails"""

    _response: Response | None
    _message: str | None

    def __init__(self, response: Response | None = None, message: str | None = None) -> None:
        self._response = response
        self._message = message

    def detail(self) -> str:
        """Get human readable details of this error"""
        if not self._response:
            return self._message
        try:
            error = SCIMError.model_validate_json(self._response.text)
            return error.detail
        except ValidationError:
            pass
        return self._message
