"""SCIM Client exceptions"""

from pydantic import ValidationError
from requests import Response

from authentik.lib.sync.outgoing.exceptions import TransientSyncException
from authentik.providers.scim.clients.schema import SCIMError


class SCIMRequestException(TransientSyncException):
    """Exception raised when an SCIM request fails"""

    _response: Response | None
    _message: str | None

    def __init__(self, response: Response | None = None, message: str | None = None) -> None:
        super().__init__(response)
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

    def __str__(self):
        if self._response:
            return self._response.text
        return super().__str__()
