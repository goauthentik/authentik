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
        self._message = message or self.error_default

    def detail(self) -> str:
        """Get human readable details of this error"""
        # requests.Response is falsy for 4xx/5xx responses, so check for None explicitly
        if self._response is None:
            return self._message
        try:
            error = SCIMError.model_validate_json(self._response.text)
            return error.detail or self._message
        except ValidationError:
            pass
        return self._response.text or self._message

    def __str__(self):
        return self.detail()

    def __repr__(self):
        return self.detail()
