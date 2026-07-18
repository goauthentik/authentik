from json import dumps

from httplib2 import Response


class MockHTTP:

    _recorded_requests = []
    _responses = {}

    def __init__(
        self,
        raise_on_unrecorded=True,
    ) -> None:
        self._recorded_requests = []
        self._responses = {}
        self.raise_on_unrecorded = raise_on_unrecorded

    def add_response(self, uri: str, body: str | dict = "", meta: dict | None = None, method="GET"):
        if isinstance(body, dict):
            body = dumps(body)
        self._responses[(uri, method.upper())] = (body, meta or {"status": "200"})

    def requests(self):
        return self._recorded_requests

    def request(
        self,
        uri,
        method="GET",
        body=None,
        headers=None,
        redirections=1,
        connection_type=None,
    ):
        key = (uri, method.upper())
        self._recorded_requests.append((uri, method, body, headers))
        if key not in self._responses and self.raise_on_unrecorded:
            raise AssertionError(key)
        body, meta = self._responses[key]
        return Response(meta), body.encode("utf-8")
