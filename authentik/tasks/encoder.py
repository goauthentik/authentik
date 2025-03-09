import jsonpickle
import dramatiq.encoder
from typing import Any
from dramatiq.encoder import MessageData
import orjson


class OrjsonBackend(jsonpickle.JSONBackend):
    def encode(self, obj: Any, indent=None, separators=None) -> str:
        return orjson.dumps(obj, option=orjson.OPT_NON_STR_KEYS).decode("utf-8")

    def decode(self, string: str) -> Any:
        return orjson.loads(string)


class JSONPickleEncoder(dramatiq.encoder.Encoder):
    def encode(self, data: MessageData) -> bytes:
        return jsonpickle.encode(
            data,
            backend=OrjsonBackend(),
            keys=True,
            warn=True,
            use_base85=True,
        ).encode("utf-8")

    def decode(self, data: bytes) -> MessageData:
        return jsonpickle.decode(
            data.decode("utf-8"),
            backend=OrjsonBackend(),
            keys=True,
            on_missing="warn",
        )
