"""SCIM Client exceptions"""
from typing import Optional

from pydantic import ValidationError
from pydanticscim.responses import SCIMError
from requests import Response

from authentik.lib.sentry import SentryIgnoredException


class StopSync(SentryIgnoredException):
    """Exception raised when a configuration error should stop the sync process"""

    def __init__(self, exc: Exception, obj: object, mapping: Optional[object] = None) -> None:
        self.exc = exc
        self.obj = obj
        self.mapping = mapping

    def __str__(self) -> str:
        msg = f"Error {str(self.exc)}, caused by {self.obj}"

        if self.mapping:
            msg += f" (mapping {self.mapping})"
        return msg


class SCIMRequestException(SentryIgnoredException):
    """Exception raised when an SCIM request fails"""

    _response: Optional[Response]

    def __init__(self, response: Optional[Response] = None) -> None:
        self._response = response

    def __str__(self) -> str:
        if not self._response:
            return super().__str__()
        try:
            error = SCIMError.parse_raw(self._response.text)
            return error.detail
        except ValidationError:
            pass
        return super().__str__()


class ResourceMissing(SCIMRequestException):
    """Error raised when the provider raises a 404, meaning that we
    should delete our internal ID and re-create the object"""
