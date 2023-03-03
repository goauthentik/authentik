"""SCIM Client exceptions"""
from pydantic import ValidationError
from pydanticscim.responses import SCIMError
from requests import Response

from authentik.lib.sentry import SentryIgnoredException


class SCIMRequestError(SentryIgnoredException):
    """Error raised when an SCIM request fails"""

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
