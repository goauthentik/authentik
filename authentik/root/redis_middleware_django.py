"""Make Django use custom Redis client"""

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from json import dumps as json_dumps
from typing import Any
from urllib.parse import urlparse

from django_redis.client.default import DefaultClient, _main_exceptions
from django_redis.exceptions import ConnectionInterrupted
from redis import Redis
from redis.cluster import RedisCluster

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)


class CustomClient(DefaultClient):
    """Custom client in order to use custom Redis URL parser

    server contains the Redis configuration URL
    """

    def __init__(self, server, params, backend):
        url = urlparse(server)
        config = process_config(url, *get_redis_options(url))
        server = [config]

        if config["type"] == "sentinel":
            config_slave = deepcopy(config)
            config_slave["is_slave"] = True
            server.append(config_slave)

        super().__init__(server, params, backend)

    def connect(self, index: int = 0):
        """
        Given a connection index, returns a new raw Redis client/connection
        instance. Index is used for replication setups and indicates that
        connection string should be used. In normal setups, index is 0.
        """
        config = self._server[index]
        return self.connection_factory.connect(config)

    def get_many(self, keys, version: int | None = None, client=None) -> OrderedDict:
        """
        Retrieve many keys.
        """
        if self._server[0]["type"] != "cluster":
            return super().get_many(keys, version, client)

        if not keys:
            return OrderedDict()

        if client is None:
            client = self.get_client(write=False)

        recovered_data = OrderedDict()

        map_keys = OrderedDict((self.make_key(k, version=version), k) for k in keys)

        try:
            pipeline = client.pipeline()
            for key in map_keys:
                pipeline.get(key)
            results = pipeline.execute()
        except _main_exceptions as exc:
            raise ConnectionInterrupted(connection=client) from exc

        for key, value in zip(map_keys, results, strict=False):
            if value is None:
                continue
            recovered_data[map_keys[key]] = self.decode(value)
        return recovered_data

    def keys(
        self, search: str, version: int | None = None, client: Redis | None = None
    ) -> list[Any]:
        """
        Execute KEYS command and return matched results.
        Warning: this can return huge number of results, in
        this case, it strongly recommended use iter_keys
        for it.
        """
        if self._server[0]["type"] != "cluster":
            return super().keys(search, version, client)

        try:
            return [*self.iter_keys(search)]
        except _main_exceptions as exc:
            raise ConnectionInterrupted(connection=client) from exc

    def delete_many(self, keys, version: int | None = None, client=None):
        """
        Remove multiple keys at once.
        """
        if self._server[0]["type"] != "cluster":
            return super().delete_many(keys, version, client)

        if client is None:
            client = self.get_client(write=False)

        try:
            pipeline = client.pipeline()
            for key in [self.make_key(k, version=version) for k in keys]:
                pipeline.delete(key)
            return sum(pipeline.execute())
        except _main_exceptions as exc:
            raise ConnectionInterrupted(connection=client) from exc


class CustomConnectionFactory:
    """Store connection pools by hashing backend options.

    _pool_cache is a process-global, as otherwise _pool_cache is cleared every time
    ConnectionFactory is instantiated, as Django creates new cache client
    (DefaultClient) instance for every request.
    """

    _pool_cache = {}

    def __init__(self, options):
        self.options = options

    def __del__(self):
        for pool, _ in self._pool_cache.values():
            if pool is not None:
                pool.disconnect()

    def connect(self, config: dict):
        """
        Given a basic connection parameters,
        return a new connection.
        """
        checksum = sha256(json_dumps(config, sort_keys=True).encode("utf-8")).hexdigest()
        pool, client_config = self._pool_cache.setdefault(checksum, get_connection_pool(config))
        return get_client(client_config, pool)

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
