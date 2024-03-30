"""Make Celery use custom Redis backend and message queue"""

from urllib.parse import urlparse

from celery.app.backends import by_url as backends_by_url
from celery.backends.redis import RedisBackend, ResultConsumer
from structlog.stdlib import get_logger
from tenant_schemas_celery.app import CeleryApp as TenantAwareCeleryApp

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)
from authentik.root.redis_middleware_kombu import CustomConnection

logger = get_logger(__name__)


class CustomResultConsumer(ResultConsumer):
    """Custom result consumer with Redis cluster support"""

    def on_after_fork(self):
        """Clear state for child processes"""
        try:
            if self.backend.uses_cluster:
                self.backend.client.nodes_manager.reset()
            else:
                self.backend.client.connection_pool.reset()
            if self._pubsub is not None:
                self._pubsub.close()
        except KeyError as exc:
            logger.warning(str(exc))
        super().on_after_fork()

    def _reconnect_pubsub(self):
        """Reconnect failing pubsub connections"""
        self._pubsub = None
        if self.backend.uses_cluster:
            self.backend.client.nodes_manager.reset()
        else:
            self.backend.client.connection_pool.reset()
        # Task state might have changed when the connection was down, so we
        # retrieve meta for all subscribed tasks before going into pubsub mode
        slots = {}
        if (
            self.subscribed_to
            and hasattr(self.backend.client, "keyslot")
            and callable(getattr(self.backend.client, "keyslot", None))
        ):
            slots = {self.backend.client.keyslot(key) for key in self.subscribed_to}

        if len(slots) > 1:
            pipe = self.backend.client.pipeline()
            for key in self.subscribed_to:
                pipe.get(key)
            metas = pipe.execute()
        else:
            metas = self.backend.client.mget(self.subscribed_to)

        metas = [meta for meta in metas if meta]
        for meta in metas:
            self.on_state_change(self._decode_result(meta), None)
        self._pubsub = self.backend.client.pubsub(
            ignore_subscribe_messages=True,
        )
        # subscribed_to maybe empty after on_state_change
        if self.subscribed_to:
            self._pubsub.subscribe(*self.subscribed_to)
        else:
            if self.backend.uses_cluster:
                if self._pubsub.connection_pool is None:
                    # Get a random node
                    node = self._pubsub.cluster.get_random_node()
                    self._pubsub.node = node
                    redis_connection = self._pubsub.cluster.get_redis_connection(node)
                    self._pubsub.connection_pool = redis_connection.connection_pool

            self._pubsub.connection = self._pubsub.connection_pool.get_connection(
                "pubsub", self._pubsub.shard_hint
            )
            # Even if there is nothing to subscribe,
            # we should not lose the callback after connecting.
            # The on_connect callback will re-subscribe to
            # any channels we previously subscribed to.
            self._pubsub.connection._register_connect_callback(self._pubsub.on_connect)


class CustomBackend(RedisBackend):
    """Custom Redis backend in order to use custom Redis URL parser"""

    ResultConsumer = CustomResultConsumer

    def __init__(self, url=None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        url = urlparse(url)
        self.config = process_config(url, *get_redis_options(url))

    def _create_client(self, **kwargs):
        """Create new Redis client"""
        pool, client_config = self._get_pool()
        return get_client(client_config, pool)

    def _get_pool(self, **params):
        """Generate ConnectionPool using config"""
        return get_connection_pool(self.config)

    def mget(self, keys):
        if hasattr(self.client, "keyslot") and callable(getattr(self.client, "keyslot", None)):
            slots = {self.client.keyslot(key) for key in keys}
            if len(slots) != 1:
                pipe = self.client.pipeline()
                for key in keys:
                    pipe.get(key)
                return pipe.execute()
        return self.client.mget(keys)

    @property
    def uses_cluster(self) -> bool:
        """Check whether Redis cluster connection is used"""
        return self.config["type"] == "cluster"

    def _set(self, key, value):
        """Do not use pipeline publish as it is unsupported by cluster"""
        if self.uses_cluster:
            self.client.set(key, value)

            if hasattr(self, "expires"):
                self.client.expire(key, self.expires)
        else:
            super()._set(key, value)


class CustomCelery(TenantAwareCeleryApp):
    """Inject custom Redis URL parser into Celery

    While by default redis will be used as the backend,
    this implementation still allows different configurations.
    We also override the sentinel:// style URL for coherence,
    but this is not a supported URL scheme
    ==> Use redis(s)+sentinel:// instead!
    """

    def _get_backend(self):
        """Return backend based on which scheme has been specified in the URL"""
        loader = self.loader
        loader.override_backends = {
            "redis": "authentik.root.redis_middleware_celery:CustomBackend",
            "rediss": "authentik.root.redis_middleware_celery:CustomBackend",
            "sentinel": "authentik.root.redis_middleware_celery:CustomBackend",
        }
        url = self.backend_cls or self.conf.result_backend
        backend, _ = backends_by_url(url, loader)
        return backend(app=self, url=url)

    def _connection(self, url, **kwargs):
        """Return Kombu connection based on URL scheme"""
        if url and "://" in url:
            scheme, _, _ = url.partition("://")
            if "+" in scheme:
                backend, _ = url.split("+", 1)
            else:
                backend = scheme
            if backend in ["redis", "rediss"]:
                return CustomConnection(url, **kwargs)
        return super()._connection(url, **kwargs)
