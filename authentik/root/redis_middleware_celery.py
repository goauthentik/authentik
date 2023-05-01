"""Make Celery use custom Redis backend and message queue"""
from urllib.parse import urlparse

from celery import Celery
from celery.app.backends import by_url as backends_by_url
from celery.backends.redis import RedisBackend

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)
from authentik.root.redis_middleware_kombu import CustomConnection


class CustomBackend(RedisBackend):
    def __init__(self, url=None, **kwargs):
        super().__init__(**kwargs)
        self.url = url
        url = urlparse(url)
        self.config = process_config(url, *get_redis_options(url))

    def _create_client(self, **kwargs):
        pool, client_config = self._get_pool()
        return get_client(client_config, pool)

    def _get_pool(self, **params):
        return get_connection_pool(self.config)


class CustomCelery(Celery):
    # While by default redis will be used as the backend,
    # this implementation still allows different configurations.
    # We also override the sentinel:// style URL for coherence,
    # but this is not a supported URL scheme
    # ==> Use redis(s)+sentinel:// instead!
    def _get_backend(self):
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
        if url and "://" in url:
            scheme, _, _ = url.partition("://")
            if "+" in scheme:
                backend, _ = url.split("+", 1)
            else:
                backend = scheme
            if backend in ["redis", "rediss"]:
                return CustomConnection(url, **kwargs)
        return super()._connection(url, **kwargs)
