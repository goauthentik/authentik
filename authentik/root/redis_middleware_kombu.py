"""Make Kombu use custom Redis connection"""

from contextlib import contextmanager
from queue import Empty
from time import time
from urllib.parse import urlparse

from kombu import Connection
from kombu.transport import virtual
from kombu.transport.redis import Channel, MultiChannelPoller, MutexHeld, Transport
from kombu.transport.redis import QoS as RedisQoS
from kombu.utils import uuid
from kombu.utils.collections import HashedSeq
from kombu.utils.compat import _detect_environment
from kombu.utils.encoding import bytes_to_str
from kombu.utils.eventio import ERR, READ
from kombu.utils.json import loads
from redis.exceptions import MovedError

from authentik.lib.utils.parser import (
    get_client,
    get_connection_pool,
    get_redis_options,
    process_config,
)


@contextmanager
def mutex(client, name, expire):
    """
    Use custom Mutex in order to support Redis Cluster: https://github.com/celery/kombu/pull/1021
    Copied from `kombu.transport.redis` and disable pipeline transcation
    """
    lock_id = uuid().encode("utf-8")
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


class CustomQoS(RedisQoS):
    """Copied from `kombu.transport.redis` to replace `Mutex` implementation."""

    def restore_visible(self, start=0, num=10, interval=10):
        """Use custom mutex for restoring visible"""
        with self.channel.conn_or_acquire() as client:
            ceil = time() - self.visibility_timeout

            try:
                with mutex(
                    client,
                    self.unacked_mutex_key,
                    self.unacked_mutex_expire,
                ):
                    env = _detect_environment()
                    if env == "gevent":
                        ceil = time()

                    visible = client.zrevrangebyscore(
                        self.unacked_index_key,
                        ceil,
                        0,
                        start=num and start,
                        num=num,
                        withscores=True,
                    )

                    for tag, _ in visible or []:
                        self.restore_by_tag(tag, client)
            except MutexHeld:
                pass

    def restore_by_tag(self, tag, client=None, leftmost=False):
        """Redis cluster does not support transactions or pipeline multi"""
        with self.channel.conn_or_acquire(client) as channel_client:
            with channel_client.pipeline() as pipe:
                result, _, _ = self._remove_from_indices(
                    tag, pipe.hget(self.unacked_key, tag)
                ).execute()
            if result:
                payload, exchange, routing_key = loads(bytes_to_str(result))  # json is unicode
                self.channel._do_restore_message(
                    payload, exchange, routing_key, channel_client, leftmost
                )


class ClusterPoller(MultiChannelPoller):
    """Custom async I/O poller with Redis cluster support for Redis transport"""

    def _register(self, channel, client, conn, cmd):
        """Register the poller and make connection"""
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
        """Unregister the poller"""
        sock = self._chan_to_sock[(channel, client, conn, cmd)]
        self.poller.unregister(sock)

    def _register_BRPOP(self, channel):
        """Register poller and start BRPOP"""
        conns = self._get_conns_for_channel(channel)

        for conn in conns:
            ident = (channel, channel.client, conn, "BRPOP")

            if conn._sock is None or ident not in self._chan_to_sock:
                channel._in_poll = False
                self._register(*ident)

        if not channel._in_poll:  # send BRPOP
            channel._brpop_start()

    def _get_conns_for_channel(self, channel):
        """Get all connections for a specific channel"""
        if self._chan_to_sock:
            return [conn for _, _, conn, _ in self._chan_to_sock]

        conns = []

        for key in channel.active_queues:
            node = channel.client.get_node_from_key(key)
            conns += [channel.client.get_redis_connection(node).connection_pool.get_connection("_")]

        return conns

    def _on_poll_start(self):
        raise NotImplementedError()

    # pylint: disable=inconsistent-return-statements
    def handle_event(self, fileno, event):
        """Handle an event"""
        if event & READ:
            return self.on_readable(fileno), self
        if event & ERR:
            chan, conn, cmd = self._fd_to_chan[fileno]
            chan._poll_error(cmd, conn)

    # pylint: disable=inconsistent-return-statements
    def on_readable(self, fileno):
        """Handle read event"""
        try:
            chan, conn, cmd = self._fd_to_chan[fileno]
        except KeyError:
            return

        if chan.qos.can_consume():
            return chan.handlers[cmd](**{"conn": conn})


class CustomChannel(Channel):
    """Enable usage of any valid Redis client as Kombu channel"""

    QoS = RedisQoS

    def __init__(self, *args, **kwargs):
        self.client_config = None
        self.config = args[0].client.config
        super().__init__(*args, **kwargs)
        del self.Client

    def inject_custom_connection_class(self, connection_class):
        """Connection injection that is required for Kombu async pools"""

        channel_handle_disconnect = self._on_connection_disconnect

        class AsyncConnection(connection_class):
            """Kombu injection for async connections"""

            def disconnect(self):
                """Add Kombu method to default disconnect procedure"""
                super().disconnect()
                channel_handle_disconnect(self)

        return AsyncConnection

    def _create_client(self, asynchronous=False):
        """Create a new Redis client using the stored connection pool"""
        if asynchronous:
            pool = self.async_pool
        else:
            pool = self.pool
        return get_client(self.client_config, pool)

    def _get_pool(self, asynchronous=False):
        """Create a new connection pool using parsed Redis config"""
        pool, client_config = get_connection_pool(
            self.config,
            use_async=False,
            update_connection_class=self.inject_custom_connection_class if asynchronous else None,
        )
        self.client_config = client_config
        return pool

    def exchange_bind(self, *args, **kwargs):
        """Bind an exchange to an exchange.

        Raises:
            NotImplementedError: as exchange_bind
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support exchange_bind.")

    def exchange_unbind(self, *args, **kwargs):
        """Unbind an exchange from an exchange.

        Raises:
            NotImplementedError: as exchange_unbind
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support exchange_unbind.")

    def flow(self, active=True):
        """Enable/disable message flow.

        Raises:
            NotImplementedError: as flow
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support flow.")


class CustomClusterChannel(Channel):
    """Enable usage of any valid Redis client as Kombu channel"""

    QoS = CustomQoS

    socket_keepalive = True

    namespace = "default"
    keyprefix_queue = "/{namespace}/_kombu/binding%s"
    keyprefix_fanout = "/{namespace}/_kombu/fanout."
    unacked_key = "/{namespace}/_kombu/unacked"
    unacked_index_key = "/{namespace}/_kombu/unacked_index"
    unacked_mutex_key = "/{namespace}/_kombu/unacked_mutex"

    min_priority = 0
    max_priority = 0
    priority_steps = [min_priority]

    from_transport_options = Channel.from_transport_options + (
        "namespace",
        "keyprefix_queue",
        "keyprefix_fanout",
    )

    def __init__(self, conn, *args, **kwargs):
        self.client_config = None
        self.config = conn.client.config
        options = conn.client.transport_options
        namespace = options.get("namespace", self.namespace)
        keys = [
            "keyprefix_queue",
            "keyprefix_fanout",
            "unacked_key",
            "unacked_index_key",
            "unacked_mutex_key",
        ]

        for key in keys:
            value = options.get(key, getattr(self, key))
            options[key] = value.format(namespace=namespace)

        super().__init__(conn, *args, **kwargs)
        self.client.info()

    def inject_custom_connection_class(self, connection_class):
        """Connection injection that is required for Kombu async pools"""

        class AsyncConnection(connection_class):
            """Kombu injection for async connections"""

            def disconnect(self):
                """Add Kombu method to default disconnect procedure"""
                super().disconnect()
                self._on_connection_disconnect(self)

        return AsyncConnection

    def _create_client(self, asynchronous=False):
        """Create a new Redis client using the stored connection pool"""
        if asynchronous:
            pool = self.async_pool
        else:
            pool = self.pool
        return get_client(self.client_config, pool)

    def _get_pool(self, asynchronous=False):
        """Create a new connection pool using parsed Redis config"""
        pool, client_config = get_connection_pool(
            self.config,
            use_async=False,
            update_connection_class=self.inject_custom_connection_class if asynchronous else None,
        )
        self.client_config = client_config
        return pool

    def exchange_bind(self, *args, **kwargs):
        """Bind an exchange to an exchange.

        Raises:
            NotImplementedError: as exchange_bind
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support exchange_bind.")

    def exchange_unbind(self, *args, **kwargs):
        """Unbind an exchange from an exchange.

        Raises:
            NotImplementedError: as exchange_unbind
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support exchange_unbind.")

    def flow(self, active=True):
        """Enable/disable message flow.

        Raises:
            NotImplementedError: as flow
                is not implemented by the base virtual implementation.
        """
        raise NotImplementedError("Redis channels do not support flow.")

    def _brpop_start(self, timeout=1):
        """Start blocking list pop primitive."""
        queues = self._queue_cycle.consume(len(self.active_queues))
        if not queues:
            return

        self._in_poll = True
        timeout = timeout or 0
        node_to_keys = {}

        for key in queues:
            node = self.client.get_node_from_key(key)
            node_to_keys.setdefault(node.name, []).append(key)

        for chan, client, conn, cmd in self.connection.cycle._chan_to_sock:
            expected = (self, self.client, "BRPOP")
            keys = node_to_keys.get(client.get_node(conn.host, conn.port).name)

            if keys and (chan, client, cmd) == expected:
                for key in keys:
                    conn.send_command("BRPOP", key, timeout)

    def _brpop_read(self, **options):
        """Read data from blocking list pop primitive."""
        client = self.client
        conn = options.pop("conn", None)

        if conn is not None:
            try:
                resp = client.get_node(conn.host, conn.port).redis_connection.parse_response(
                    conn, "BRPOP", **options
                )
            except self.connection_errors:
                conn.disconnect()
                raise
            except MovedError as exc:
                # copied from rediscluster/client.py
                client.reinitialize_counter += 1
                if client._should_reinitialized():
                    client.nodes_manager.initialize()
                    # Reset the counter
                    client.reinitialize_counter = 0
                else:
                    client.nodes_manager.update_moved_exception(exc)
                raise Empty() from None

            if resp:
                dest, item = resp
                dest = bytes_to_str(dest).rsplit(self.sep, 1)[0]
                self._queue_cycle.rotate(dest)
                self.connection._deliver(loads(bytes_to_str(item)), dest)
                return True

        self._in_poll = False
        return False

    def _poll_error(self, cmd, conn, **options):
        """Check for BRPOP error"""
        if cmd == "BRPOP":
            self.client.parse_response(conn, cmd)


class CustomTransport(Transport):
    """Inject custom cluster poller and custom channel for full Redis client support"""

    Channel = CustomChannel

    def as_uri(self, uri: str, include_password=False, mask="**") -> str:
        """Customise the display format of the URI."""
        raise NotImplementedError()


class CustomClusterTransport(Transport):
    """Inject custom cluster poller and custom channel for full Redis cluster client support"""

    Channel = CustomClusterChannel

    driver_type = "redis-cluster"
    driver_name = "redis-cluster"

    implements = virtual.Transport.implements.extend(
        asynchronous=True, exchange_type=frozenset(["direct"])
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cycle = ClusterPoller()

    def as_uri(self, uri: str, include_password=False, mask="**") -> str:
        """Customise the display format of the URI."""
        raise NotImplementedError()


class CustomConnection(Connection):
    """Used to inject custom Redis client into Kombu"""

    def __init__(self, url, **kwargs):
        kwargs.setdefault("hostname", None)
        kwargs["url"] = url
        super().__init__(**kwargs)
        self._init_params(**kwargs)

    def _init_params(self, **kwargs):
        """Parse Redis URL into config dict and store it"""
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
        """Return the Redis config describing the connection"""
        return self.config

    def clone(self, **kwargs):
        """Create a copy of the connection with same settings."""
        return self.__class__(self.url, **kwargs)

    def __eqhash__(self):
        """Return hashed sequence in order to prevent hash to be called multiple times"""
        return HashedSeq(repr(self.config))

    def as_uri(self, **kwargs):
        """Return Redis configuration URL"""
        return self.url

    @property
    def host(self):
        """Get host name/port pair separated by colon."""
        return ":".join(self.config["addrs"][0])

    @property
    def _uses_cluster(self) -> bool:
        """Check whether Redis cluster connection is used"""
        return self.config["type"] == "cluster"

    def create_transport(self):
        """Create custom transport for full Redis client support"""
        if self._uses_cluster:
            return CustomClusterTransport(client=self)
        return CustomTransport(client=self)

    def get_transport_cls(self):
        """Get the currently used transport class."""
        if self._uses_cluster:
            return CustomClusterTransport
        return CustomTransport

    @property
    def transport(self):
        """Cache custom transport"""
        if self._transport is None:
            self._transport = self.create_transport()
        return self._transport
