from base64 import b64decode
from dataclasses import asdict, dataclass
from random import choice
from typing import Any
from uuid import uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels_redis.pubsub import RedisPubSubChannelLayer
from requests.adapters import BaseAdapter
from requests.models import PreparedRequest, Response
from structlog.stdlib import get_logger
from requests.utils import CaseInsensitiveDict
from authentik.outposts.models import Outpost


@dataclass
class OutpostPreparedRequest:
    uid: str
    method: str
    url: str
    headers: dict[str, str]
    body: Any
    ssl_verify: bool
    timeout: int

    @staticmethod
    def from_requests(req: PreparedRequest) -> "OutpostPreparedRequest":
        return OutpostPreparedRequest(
            uid=str(uuid4()),
            method=req.method,
            url=req.url,
            headers=req.headers._store,
            body=req.body,
            ssl_verify=True,
            timeout=0,
        )

    @property
    def response_channel(self) -> str:
        return f"authentik_outpost_http_response_{self.uid}"

class OutpostHTTPAdapter(BaseAdapter):
    """Requests Adapter that sends HTTP requests via a specified Outpost"""

    def __init__(self, outpost: Outpost, default_timeout=10):
        super().__init__()
        self.__outpost = outpost
        self.__logger = get_logger().bind()
        self.__layer: RedisPubSubChannelLayer = get_channel_layer()
        self.default_timeout = default_timeout

    def parse_response(self, raw_response: dict, req: PreparedRequest) -> Response:
        res = Response()
        res.request = req
        res.status_code = raw_response.get("status")
        res.url = raw_response.get("final_url")
        res.headers = CaseInsensitiveDict(raw_response.get("headers"))
        res._content = b64decode(raw_response.get("body"))
        return res

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        # Convert request so we can send it to the outpost
        converted = OutpostPreparedRequest.from_requests(request)
        converted.ssl_verify = verify
        converted.timeout = timeout if timeout else self.default_timeout
        # Pick one of the outpost instances
        state = choice(self.__outpost.state)
        self.__logger.debug("sending HTTP request to outpost", uid=converted.uid)
        async_to_sync(self.__layer.send)(
            state.uid,
            {
                "type": "event.provider.specific",
                "sub_type": "http_request",
                "response_channel": converted.response_channel,
                "request": asdict(converted),
            },
        )
        self.__logger.debug("receiving HTTP response from outpost",uid=converted.uid)
        raw_response = async_to_sync(self.__layer.receive)(
            converted.response_channel,
        )
        self.__logger.debug("received HTTP response from outpost",uid=converted.uid)
        return self.parse_response(raw_response.get("args", {}).get("response", {}), request)
