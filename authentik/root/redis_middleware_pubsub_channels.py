"""Make pub sub channels use custom Redis layer"""

import asyncio
import logging
from copy import deepcopy
from urllib.parse import urlparse

from channels_redis.pubsub import (
    RedisPubSubChannelLayer,
    RedisPubSubLoopLayer,
    RedisSingleShardConnection,
)
from channels_redis.utils import _close_redis, _wrap_close

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)

logger = logging.getLogger(__name__)


class CustomPubSubChannelLayer(RedisPubSubChannelLayer):
    """
    Custom Redis pub sub channel layer to allow for improved Redis client support
    """

    def _get_layer(self):
        loop = asyncio.get_running_loop()

        try:
            layer = self._layers[loop]
        except KeyError:
            layer = CustomPubSubLoopLayer(
                *self._args,
                **self._kwargs,
                channel_layer=self,
            )
            self._layers[loop] = layer
            _wrap_close(self, loop)

        return layer


class CustomPubSubLoopLayer(RedisPubSubLoopLayer):
    """
    Custom pub sub loop layer to allow for improved Redis client support
    """

    def __init__(
        self,
        url=None,
        prefix="asgi",
        on_disconnect=None,
        on_reconnect=None,
        channel_layer=None,
        **kwargs,
    ):
        super().__init__([], prefix, on_disconnect, on_reconnect, channel_layer, **kwargs)
        url = urlparse(url)
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        scheme_parts = url.scheme.split("+")
        is_cluster = len(scheme_parts) > 1 and scheme_parts[1] in ["cluster", "clusters"]
        if not is_cluster:
            self._shards = []
            for index in range(len(redis_kwargs["addrs"])):
                new_redis_kwargs = deepcopy(redis_kwargs)
                new_redis_kwargs["addrs"] = [redis_kwargs["addrs"][index]]
                config = process_config(url, pool_kwargs, new_redis_kwargs, tls_kwargs)
                self._shards.append(CustomSingleShardConnection(config, self))
        else:
            raise NotImplementedError(
                "Redis cluster does currently not support asyncio pubsub connections"
            )
            # redis_options = (pool_kwargs, redis_kwargs, tls_kwargs)
            # self._shards = [
            #     CustomSingleShardConnection(
            #         process_config(url, *redis_options),
            #         self
            #     )
            # ]


class CustomSingleShardConnection(RedisSingleShardConnection):
    """
    Custom single connection to a Redis host

    When using a cluster will use the default Redis cluster implementation instead
    """

    def __init__(self, config, channel_layer):
        super().__init__(None, channel_layer)
        self.config = config
        if self.config["type"] == "cluster":
            raise NotImplementedError(
                "Redis cluster does currently not support asyncio pubsub connections"
            )

    async def flush(self):
        async with self._lock:
            if self._receive_task is not None:
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
                self._receive_task = None
            if self._redis is not None:
                # The pool was created just for this client, so make sure it is closed,
                # otherwise it will schedule the connection to be closed inside the
                # __del__ method, which doesn't have a loop running anymore.
                if self.config["type"] != "cluster":
                    await _close_redis(self._redis)
                else:
                    try:
                        await self._redis.aclose()
                    except AttributeError:
                        await self._redis.close()
                self._redis = None
                self._pubsub = None
            self._subscribed_to = set()

    def _ensure_redis(self):
        if self._redis is None:
            pool, client_config = get_connection_pool(
                self.config, use_async=self.config["type"] != "cluster"
            )
            self._redis = get_client(client_config, pool)
            self._pubsub = self._redis.pubsub()
