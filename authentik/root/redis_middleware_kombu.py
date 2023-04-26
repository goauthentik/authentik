from contextlib import contextmanager
from time import time
from urllib.parse import urlparse

from kombu import Connection
from kombu.transport import virtual
from kombu.transport.redis import Transport, MultiChannelPoller
from kombu.transport.redis import Channel, MutexHeld, QoS as RedisQoS
from kombu.utils import uuid
from kombu.utils.collections import HashedSeq
from kombu.utils.compat import _detect_environment
from kombu.utils.eventio import READ, ERR

from authentik.lib.utils.parser import get_client, get_redis_options, process_config, get_connection_pool


# Use custom Mutex in order to support Redis Cluster: https://github.com/celery/kombu/pull/1021
# Copied from `kombu.transport.redis` and disable pipeline transcation
@contextmanager
def Mutex(client, name, expire):
    lock_id = uuid().encode('utf-8')
    acquired = client.set(name, lock_id, ex=expire, nx=True)

    try:
        if acquired:
            yield
        else:
            raise MutexHeld()
    finally:
        if acquired:
            if client.get(name) == lock_id:
                client.delete(name)


# Copied from `kombu.transport.redis` to replace `Mutex` implementation.
class CustomQoS(RedisQoS):
    def restore_visible(self, start=0, num=10, interval=10):
        with self.channel.conn_or_acquire() as client:
            ceil = time() - self.visibility_timeout

            try:
                with Mutex(
                    client,
                    self.unacked_mutex_key,
                    self.unacked_mutex_expire,
                ):
                    env = _detect_environment()
                    if env == 'gevent':
                        ceil = time()

                    visible = client.zrevrangebyscore(
                        self.unacked_index_key,
                        ceil,
                        0,
                        start=num and start,
                        num=num,
                        withscores=True
                    )

                    for tag, score in visible or []:
                        self.restore_by_tag(tag, client)
            except MutexHeld:
                pass


class ClusterPoller(MultiChannelPoller):

    def _register(self, channel, client, conn, cmd):
        ident = (channel, client, conn, cmd)

        if ident in self._chan_to_sock:
            self._unregister(*ident)

        if conn._sock is None:
            conn.connect()

        sock = conn._sock
        self._fd_to_chan[sock.fileno()] = (channel, conn, cmd)
        self._chan_to_sock[ident] = sock
        self.poller.register(sock, self.eventflags)

    def _unregister(self, channel, client, conn, cmd):
        sock = self._chan_to_sock[(channel, client, conn, cmd)]
        self.poller.unregister(sock)

    def _register_BRPOP(self, channel):
        conns = self._get_conns_for_channel(channel)

        for conn in conns:
            ident = (channel, channel.client, conn, 'BRPOP')

            if conn._sock is None or ident not in self._chan_to_sock:
                channel._in_poll = False
                self._register(*ident)

        if not channel._in_poll:  # send BRPOP
            channel._brpop_start()

    def _get_conns_for_channel(self, channel):
        if self._chan_to_sock:
            return [conn for _, _, conn, _ in self._chan_to_sock]

        return [
            channel.client.connection_pool.get_connection_by_key(key, 'NOOP')
            for key in channel.active_queues
        ]

    def handle_event(self, fileno, event):
        if event & READ:
            return self.on_readable(fileno), self
        elif event & ERR:
            chan, conn, cmd = self._fd_to_chan[fileno]
            chan._poll_error(cmd, conn)

    def on_readable(self, fileno):
        try:
            chan, conn, cmd = self._fd_to_chan[fileno]
        except KeyError:
            return

        if chan.qos.can_consume():
            return chan.handlers[cmd](**{'conn': conn})


class CustomChannel(Channel):
    QoS = RedisQoS

    def __init__(self, *args, **kwargs):
        self.config = args[0].client.config
        super().__init__(*args, **kwargs)
        if self.config["type"] == "cluster":
            self.QoS = CustomQoS
        del self.Client

    def inject_custom_connection_class(self, connection_class):
        class AsyncConnection(connection_class):
            def disconnect(self):
                super().disconnect()
                self._on_connection_disconnect(self)
        return AsyncConnection

    def _create_client(self, asynchronous=False):
        if asynchronous:
            pool = self.async_pool
        else:
            pool = self.pool
        return get_client(self.client_config, pool)

    def _get_pool(self, asynchronous=False):
        pool, client_config = get_connection_pool(
            self.config,
            use_async=False,
            update_connection_class=self.inject_custom_connection_class if asynchronous else None
        )
        self.client_config = client_config
        return pool


class CustomTransport(Transport):
    Channel = CustomChannel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.client.config["type"] == "cluster":
            self.implements = virtual.Transport.implements.extend(
                asynchronous=True, exchange_type=frozenset(['direct'])
            )
            self.cycle = ClusterPoller()


class CustomConnection(Connection):
    def __init__(self, url, **kwargs):
        kwargs.setdefault("hostname", None)
        kwargs["url"] = url
        super().__init__(**kwargs)
        self._init_params(**kwargs)

    def _init_params(self, **kwargs):
        self.url = kwargs.get("url")
        if self.url:
            url = urlparse(self.url)
            self.config = process_config(url, *get_redis_options(url, disable_socket_timeout=True))

    def switch(self, conn_str):
        """Switch connection parameters to use a new URL or hostname.

        Note:
            Does not reconnect!

        Arguments:
            conn_str (str): either a hostname or URL.
        """
        self.close()
        self.declared_entities.clear()
        self._closed = False
        self._init_params(url=conn_str)

    def info(self):
        return self.config

    def clone(self, **kwargs):
        """Create a copy of the connection with same settings."""
        return self.__class__(self.url, **kwargs)

    def __eqhash__(self):
        return HashedSeq(repr(self.config))

    def as_uri(self, **kwargs):
        return self.url

    @property
    def host(self):
        """The host as a host name/port pair separated by colon."""
        return ':'.join(self.config["addrs"][0])

    def create_transport(self):
        return CustomTransport(client=self)

    def get_transport_cls(self):
        """Get the currently used transport class."""
        return CustomTransport

    @property
    def transport(self):
        if self._transport is None:
            self._transport = self.create_transport()
        return self._transport
