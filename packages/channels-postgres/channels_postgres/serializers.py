import abc
import base64
import hashlib
import json
import random

try:
    from cryptography.fernet import Fernet, MultiFernet
except ImportError:
    MultiFernet = Fernet = None


class SerializerDoesNotExist(KeyError):
    """The requested serializer was not found."""


class BaseMessageSerializer(abc.ABC):
    def __init__(
        self,
        symmetric_encryption_keys=None,
        random_prefix_length=0,
        expiry=None,
    ):
        self.random_prefix_length = random_prefix_length
        self.expiry = expiry
        # Set up any encryption objects
        self._setup_encryption(symmetric_encryption_keys)

    def _setup_encryption(self, symmetric_encryption_keys):
        # See if we can do encryption if they asked
        if symmetric_encryption_keys:
            if isinstance(symmetric_encryption_keys, str | bytes):
                raise ValueError("symmetric_encryption_keys must be a list of possible keys")
            if MultiFernet is None:
                raise ValueError("Cannot run with encryption without 'cryptography' installed.")
            sub_fernets = [self.make_fernet(key) for key in symmetric_encryption_keys]
            self.crypter = MultiFernet(sub_fernets)
        else:
            self.crypter = None

    def make_fernet(self, key):
        """
        Given a single encryption key, returns a Fernet instance using it.
        """
        if Fernet is None:
            raise ValueError("Cannot run with encryption without 'cryptography' installed.")

        if isinstance(key, str):
            key = key.encode("utf-8")
        formatted_key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        return Fernet(formatted_key)

    @abc.abstractmethod
    def as_bytes(self, message, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def from_bytes(self, message, *args, **kwargs):
        raise NotImplementedError

    def serialize(self, message):
        """
        Serializes message to a byte string.
        """
        message = self.as_bytes(message)
        if self.crypter:
            message = self.crypter.encrypt(message)

        if self.random_prefix_length > 0:
            # provide random prefix
            message = (
                random.getrandbits(8 * self.random_prefix_length).to_bytes(
                    self.random_prefix_length, "big"
                )
                + message
            )
        return message

    def deserialize(self, message):
        """
        Deserializes from a byte string.
        """
        if self.random_prefix_length > 0:
            # Removes the random prefix
            message = message[self.random_prefix_length :]  # noqa: E203

        if self.crypter:
            ttl = self.expiry if self.expiry is None else self.expiry + 10
            message = self.crypter.decrypt(message, ttl)
        return self.from_bytes(message)


class MissingSerializer(BaseMessageSerializer):
    exception = None

    def __init__(self, *args, **kwargs):
        raise self.exception


class JSONSerializer(BaseMessageSerializer):
    # json module by default always produces str while loads accepts bytes
    # thus we must force bytes conversion
    # we use UTF-8 since it is the recommended encoding for interoperability
    # see https://docs.python.org/3/library/json.html#character-encodings
    def as_bytes(self, message, *args, **kwargs):
        message = json.dumps(message, *args, **kwargs)
        return message.encode("utf-8")

    from_bytes = staticmethod(json.loads)


# code ready for a future in which msgpack may become an optional dependency
try:
    import msgpack
except ImportError as exc:

    class MsgPackSerializer(MissingSerializer):
        exception = exc

else:

    class MsgPackSerializer(BaseMessageSerializer):
        as_bytes = staticmethod(msgpack.packb)
        from_bytes = staticmethod(msgpack.unpackb)


class SerializersRegistry:
    """
    Serializers registry inspired by that of ``django.core.serializers``.
    """

    def __init__(self):
        self._registry = {}

    def register_serializer(self, format, serializer_class):
        """
        Register a new serializer for given format
        """
        assert isinstance(serializer_class, type) and (
            issubclass(serializer_class, BaseMessageSerializer)
            or (hasattr(serializer_class, "serialize") and hasattr(serializer_class, "deserialize"))
        ), """
            `serializer_class` should be a class which implements `serialize` and `deserialize` method
            or a subclass of `channels_redis.serializers.BaseMessageSerializer`
        """

        self._registry[format] = serializer_class

    def get_serializer(self, format, *args, **kwargs):
        try:
            serializer_class = self._registry[format]
        except KeyError:
            raise SerializerDoesNotExist(format)

        return serializer_class(*args, **kwargs)


registry = SerializersRegistry()
registry.register_serializer("json", JSONSerializer)
registry.register_serializer("msgpack", MsgPackSerializer)
