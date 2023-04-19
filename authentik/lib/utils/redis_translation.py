from asyncio import get_running_loop, Lock
from json import dumps as json_dumps
from hashlib import sha256
from typing import Dict, Union
from urllib.parse import urlparse

from celery import Celery
from celery.backends.cache import backends
from celery.backends.redis import RedisBackend
from channels_redis.core import RedisChannelLayer
from channels_redis.utils import _wrap_close
from django_redis.client.default import DefaultClient
from redis.client import StrictRedis
from redis.cluster import RedisCluster

from lifecycle.parser import get_client, get_redis_options, process_config


class CustomBackend(RedisBackend):
    def __init__(self, url=None):
        super().__init__()
        self.url = url
        url = urlparse(url)
        self.config = process_config(url, *get_redis_options(url))

    def _create_client(self, asynchronous=False):
        return get_client(self.config)


class CustomCelery(Celery):
    # We also override the sentinel:// style URL for coherence, but this is not a supported URL scheme
    # Use redis(s)+sentinel:// instead!
    def _get_backend(self):
        loader = self.loader
        loader.override_backends = {
            "redis": "authentik.lib.utils.redis_translation:CustomBackend",
            "rediss": "authentik.lib.utils.redis_translation:CustomBackend",
            "sentinel": "authentik.lib.utils.redis_translation:CustomBackend"
        }
        backend, url = backends.by_url(
            self.backend_cls or self.conf.result_backend,
            loader)
        return backend(app=self, url=url)


class CustomLoopLayer:
    def __init__(self, channel_layer):
        self._lock = Lock()
        self.channel_layer = channel_layer
        self._connections = {}

    def get_connection(self, index):
        if index not in self._connections:
            self._connections[index] = get_client(self.channel_layer.config, use_async=True)

        return self._connections[index]

    async def flush(self):
        async with self._lock:
            for index in list(self._connections):
                connection = self._connections.pop(index)
                await connection.close(close_connection_pool=True)


class CustomChannelLayer(RedisChannelLayer):
    # hosts contains the redis configuration URL
    def __init__(
        self,
        hosts=None,
        prefix="asgi",
        expiry=60,
        group_expiry=86400,
        capacity=100,
        channel_capacity=None,
        symmetric_encryption_keys=None,
    ):
        url = urlparse(hosts)
        config = process_config(url, *get_redis_options(url, use_async=True), use_async=True)
        self.config = config
        super().__init__(config["addrs"], prefix, expiry, group_expiry, capacity, channel_capacity,
                         symmetric_encryption_keys)

    def connection(self, index):
        """
        Returns the correct connection for the index given.
        Lazily instantiates pools.
        """
        # Catch bad indexes

        if not 0 <= index < self.ring_size:
            raise ValueError(
                f"There are only {self.ring_size} hosts - you asked for {index}!"
            )

        loop = get_running_loop()
        try:
            layer = self._layers[loop]
        except KeyError:
            _wrap_close(self, loop)
            layer = self._layers[loop] = CustomLoopLayer(self)

        return layer.get_connection(index)


class CustomClient(DefaultClient):
    # server contains the redis configuration URL
    def __init__(self, server, params, backend):
        url = urlparse(server)
        config = process_config(url, *get_redis_options(url))
        server = [config]

        if config["type"] == "sentinel":
            config_slave = config.copy()
            config_slave["is_slave"] = True
            server.append(config_slave)

        super().__init__(server, params, backend)

    def connect(self, index: int = 0):
        """
        Given a connection index, returns a new raw redis client/connection
        instance. Index is used for replication setups and indicates that
        connection string should be used. In normal setups, index is 0.
        """
        config = self._server[index]
        return self.connection_factory.connect(config)


class CustomConnectionFactory:
    # Store connection pool by cache backend options.
    #
    # _client_cache is a process-global, as otherwise _client_cache is cleared every time
    # ConnectionFactory is instantiated, as Django creates new cache client
    # (DefaultClient) instance for every request.

    _client_cache: Dict[str, Union[StrictRedis, RedisCluster]] = {}

    def connect(self, config: Dict) -> Union[StrictRedis, RedisCluster]:
        """
        Given a basic connection parameters,
        return a new connection.
        """
        checksum = sha256(json_dumps(config, sort_keys=True).encode('utf-8')).hexdigest()
        return self._client_cache.setdefault(checksum, get_client(config))

    @staticmethod
    def disconnect(connection):
        """
        Given a not null client connection it disconnects from the Redis server.

        The default implementation uses a pool to hold connections.
        """
        if isinstance(connection, RedisCluster):
            connection.disconnect_connection_pools()
        else:
            connection.connection_pool.disconnect()

