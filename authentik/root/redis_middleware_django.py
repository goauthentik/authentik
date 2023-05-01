"""Make Django use custom Redis client"""
from copy import deepcopy
from hashlib import sha256
from json import dumps as json_dumps
from typing import Dict
from urllib.parse import urlparse

from django_redis.client.default import DefaultClient
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


class CustomConnectionFactory:
    """Store connection pool by cache backend options.

    _pool_cache is a process-global, as otherwise _pool_cache is cleared every time
    ConnectionFactory is instantiated, as Django creates new cache client
    (DefaultClient) instance for every request.
    """

    _pool_cache = {}

    def __init__(self, options):
        self.options = options

    def connect(self, config: Dict):
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
