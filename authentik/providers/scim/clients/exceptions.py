"""SCIM Client exceptions"""
from typing import Optional

from pydantic import ValidationError
from requests import Response

from authentik.lib.sentry import SentryIgnoredException
from authentik.providers.scim.clients.schema import SCIMError


class StopSync(SentryIgnoredException):
    """Exception raised when a configuration error should stop the sync process"""

    def __init__(self, exc: Exception, obj: object, mapping: Optional[object] = None) -> None:
        self.exc = exc
        self.obj = obj
        self.mapping = mapping

    def detail(self) -> str:
        """Get human readable details of this error"""
        msg = f"Error {str(self.exc)}, caused by {self.obj}"

        if self.mapping:
            msg += f" (mapping {self.mapping})"
        return msg


class SCIMRequestException(SentryIgnoredException):
    """Exception raised when an SCIM request fails"""

    _response: Optional[Response]
    _message: Optional[str]

    def __init__(self, response: Optional[Response] = None, message: Optional[str] = None) -> None:
        self._response = response
        self._message = message

    def detail(self) -> str:
        """Get human readable details of this error"""
        if not self._response:
            return self._message
        try:
            error = SCIMError.parse_raw(self._response.text)
            return error.detail
        except ValidationError:
            pass
        return self._message


class ResourceMissing(SCIMRequestException):
    """Error raised when the provider raises a 404, meaning that we
    should delete our internal ID and re-create the object"""
