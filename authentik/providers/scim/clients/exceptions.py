"""SCIM Client exceptions"""
from pydantic import ValidationError
from pydanticscim.responses import SCIMError
from requests import Response

from authentik.lib.sentry import SentryIgnoredException


class StopSync(SentryIgnoredException):
    """Exception raised when a configuration error should stop the sync process"""


class SCIMRequestException(SentryIgnoredException):
    """Exception raised when an SCIM request fails"""

    _response: Response

    def __init__(self, response: Response) -> None:
        self._response = response

    def __str__(self) -> str:
        try:
            error = SCIMError.parse_raw(self._response.text)
            return error.detail
        except ValidationError:
            pass
        return super().__str__()
