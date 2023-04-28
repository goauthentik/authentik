from asyncio import LifoQueue, PriorityQueue
from copy import deepcopy
from os import sched_getaffinity
from socket import TCP_KEEPCNT, TCP_KEEPINTVL
from socket import timeout as SocketTimeout
from sys import platform
from typing import Any, Dict, Tuple
from urllib.parse import ParseResultBytes, parse_qs, unquote, urlparse

from redis.asyncio.client import StrictRedis as AsyncStrictRedis
from redis.asyncio.cluster import ClusterNode as AsyncClusterNode
from redis.asyncio.cluster import RedisCluster as AsyncRedisCluster
from redis.asyncio.connection import BlockingConnectionPool as AsyncBlockingConnectionPool
from redis.asyncio.connection import Connection as AsyncConnection
from redis.asyncio.connection import SSLConnection as AsyncSSLConnection
from redis.asyncio.connection import UnixDomainSocketConnection as AsyncUnixDomainSocketConnection
from redis.asyncio.retry import Retry as AsyncRetry
from redis.asyncio.sentinel import Sentinel as AsyncSentinel
from redis.asyncio.sentinel import SentinelConnectionPool as AsyncSentinelConnectionPool
from redis.asyncio.sentinel import SentinelManagedConnection as AsyncSentinelManagedConnection
from redis.asyncio.sentinel import SentinelManagedSSLConnection as AsyncSentinelManagedSSLConnection
from redis.backoff import DEFAULT_BASE, DEFAULT_CAP, ConstantBackoff, ExponentialBackoff, NoBackoff
from redis.client import StrictRedis
from redis.cluster import ClusterNode, RedisCluster
from redis.connection import (
    BlockingConnectionPool,
    Connection,
    SSLConnection,
    UnixDomainSocketConnection,
)
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry
from redis.sentinel import (
    Sentinel,
    SentinelConnectionPool,
    SentinelManagedConnection,
    SentinelManagedSSLConnection,
)

FALSE_STRINGS = ("0", "F", "FALSE", "N", "NO")


def to_bool(value):
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.upper() in FALSE_STRINGS:
        return False
    return bool(value)


def parse_duration_to_sec(s: str) -> float:
    # This function parses a duration string into a float of seconds.
    # It supports the following units: ns, us, ms, s, m, h.
    # It returns a ValueError if the string is invalid or empty.
    if not s:
        raise ValueError("empty string")
    units = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}
    result = 0.0
    num = ""
    for c in s:
        if c.isdigit() or c == ".":
            num += c
        elif c.isalpha():
            if num == "":
                raise ValueError("invalid format")
            unit = c
            while unit not in units:
                if len(unit) == 2:
                    raise ValueError("unknown unit")
                unit = c + s[s.index(c) + 1]
            result += float(num) * units[unit]
            num = ""
        else:
            raise ValueError("invalid character")
    if num != "":
        raise ValueError("missing unit")
    return result


def val_to_sec(vs: list[bytes]):
    result = None
    for v in vs:
        try:
            result = parse_duration_to_sec(str(v))
            return result
        except ValueError:
            result = int(v)
    return result


def parse_hostport(s, default_port=6379):
    if s[-1] == "]":
        # ipv6 literal (with no port)
        return (s, default_port)

    out = s.rsplit(":", 1)
    if len(out) == 1:
        # No port
        port = default_port
    else:
        try:
            port = int(out[1])
        except ValueError:
            raise ValueError("Invalid host:port '%s'" % s)

    return out[0], port


def configure_tcp_keepalive(kwargs):
    """Set TCP keepalive on the opened sockets for redis.

    It activates after 1 second (TCP_KEEPALIVE or TCP_KEEPIDLE) of idleness,
    then sends a keepalive ping once every minute by default (TCP_KEEPINTVL),
    and closes the connection after 5 failed pings by default (TCP_KEEPCNT)
    """
    kwargs.setdefault("socket_keepalive", True)
    if platform == "darwin":
        from socket import TCP_KEEPALIVE

        activate_keepalive_sec = TCP_KEEPALIVE
    else:
        from socket import TCP_KEEPIDLE

        activate_keepalive_sec = TCP_KEEPIDLE
    kwargs.setdefault(
        "socket_keepalive_options",
        {
            activate_keepalive_sec: 5 * 60,
            TCP_KEEPINTVL: kwargs.pop("idle_check_frequency", 60),
            TCP_KEEPCNT: kwargs.pop("idle_timeout", 5 * 60)
            // kwargs.pop("idle_check_frequency", 60),
        },
    )

    return kwargs


def get_redis_options(
    url: ParseResultBytes, disable_socket_timeout=False
) -> Tuple[Dict, Dict, Dict]:
    pool_kwargs = {}
    redis_kwargs = {}
    tls_kwargs = {}

    retries_and_backoff = {}

    if url.password:
        redis_kwargs["password"] = unquote(url.password)
        if url.username:
            redis_kwargs["username"] = unquote(url.username)
    elif url.username:
        redis_kwargs["password"] = unquote(url.username)

    # TODO: Check if data type is correct for each option
    for name, value in parse_qs(url.query).items():
        if value and len(value) > 0 and isinstance(name, str):
            value_str = unquote(value[0])
            match name.lower():
                case "addr":
                    redis_kwargs.setdefault("addrs", []).extend([unquote(addr) for addr in value])
                case "addrs":
                    redis_kwargs.setdefault("addrs", []).extend(value_str.split(","))
                case "username":
                    redis_kwargs["username"] = value_str
                case "password":
                    redis_kwargs["password"] = value_str
                case "database" | "db":
                    redis_kwargs["db"] = int(value[0])
                case "maxretries":
                    retry = int(value[0])
                    if retry > 0:
                        retries_and_backoff["retry"] = retry
                        redis_kwargs["cluster_error_retry_attempts"] = retry
                    else:
                        redis_kwargs["retry"] = None
                case "minretrybackoff":
                    min_backoff = val_to_sec(value)
                    if min_backoff > 0:
                        retries_and_backoff["min_backoff"] = min_backoff
                case "maxretrybackoff":
                    max_backoff = val_to_sec(value)
                    if max_backoff > 0:
                        retries_and_backoff["max_backoff"] = max_backoff
                case "timeout":
                    timeout = val_to_sec(value)
                    if timeout <= 0:
                        timeout = None
                    if "socket_connect_timeout" not in redis_kwargs:
                        redis_kwargs["socket_connect_timeout"] = timeout
                    if "socket_timeout" not in redis_kwargs:
                        redis_kwargs["socket_timeout"] = timeout
                case "dialtimeout":
                    socket_connect_timeout = val_to_sec(value)
                    if socket_connect_timeout <= 0:
                        socket_connect_timeout = None
                    redis_kwargs["socket_connect_timeout"] = socket_connect_timeout
                case "readtimeout" | "writetimeout":
                    socket_timeout = val_to_sec(value)
                    if socket_timeout <= 0:
                        socket_timeout = None
                    if (
                        "socket_timeout" not in redis_kwargs
                        or redis_kwargs.get("socket_timeout") < socket_timeout
                    ):
                        redis_kwargs["socket_timeout"] = socket_timeout
                case "poolfifo":
                    if to_bool(value[0]):
                        pool_kwargs["queue_class"] = PriorityQueue
                    else:
                        pool_kwargs["queue_class"] = LifoQueue
                case "poolsize":
                    pool_kwargs["max_connections"] = int(value[0])
                case "pooltimeout":
                    pool_timeout = val_to_sec(value)
                    if pool_timeout <= 0:
                        pool_timeout = None
                    pool_kwargs["timeout"] = pool_timeout
                case "idletimeout":
                    redis_kwargs["idle_timeout"] = int(val_to_sec(value))
                case "idlecheckfrequency":
                    redis_kwargs["idle_check_frequency"] = int(val_to_sec(value))
                case "maxidleconns":
                    redis_kwargs["max_connections"] = int(value[0])
                case "sentinelmasterid" | "mastername":
                    redis_kwargs["service_name"] = value_str
                case "sentinelusername":
                    redis_kwargs["sentinel_username"] = value_str
                case "sentinelpassword":
                    redis_kwargs["sentinel_password"] = value_str
                case "readonly":
                    redis_kwargs["readonly"] = to_bool(value_str)
                case "skipverify":
                    if to_bool(value_str):
                        tls_kwargs["ssl_cert_reqs"] = "optional"
                case "insecureskipverify":
                    if to_bool(value_str):
                        tls_kwargs["ssl_cert_reqs"] = "none"
                # Later on use .readonly() on the resulting redis object!
                case "minidleconns" | "maxredirects" | "routebylatency" | "routerandomly":
                    print(
                        'The configuration option "'
                        + name.lower()
                        + '" is currently not supported by the Python redis implementation and therefore ignored.'
                    )
                case _:
                    raise ValueError(
                        'Detected unknown configuration option "'
                        + name.lower()
                        + '"! Please check your configuration.'
                    )

    redis_kwargs["retry"] = retries_and_backoff
    redis_kwargs.setdefault("cluster_error_retry_attempts", 3)
    redis_kwargs.setdefault("socket_connect_timeout", 5)
    redis_kwargs.setdefault("socket_timeout", 3)

    if disable_socket_timeout:
        redis_kwargs["socket_timeout"] = None

    redis_kwargs = configure_tcp_keepalive(redis_kwargs)

    if url.hostname:
        host = unquote(url.netloc).split("@")
        if len(host) > 1:
            host = host[-1]
        else:
            host = host[0]
        redis_kwargs.setdefault("addrs", []).extend(host.split(","))

    if url.path and url.scheme != "redis+socket":
        path = unquote(url.path)[1:]
        if path.isdigit():
            redis_kwargs["db"] = int(path)

    try:
        # Retreive the number of cpus that can be used
        max_connections = len(sched_getaffinity(0)) * 10
    except AttributeError:
        # Use default value of BlockingConnectionPool
        max_connections = 50
        pass

    new_addrs = []
    default_port = 26379 if "sentinel" in str(url.scheme) else 6379
    for addr in redis_kwargs.get("addrs", []):
        try:
            new_addrs.append(parse_hostport(addr, default_port))
        except ValueError:
            print("Skipping due to invalid format for a hostname and port: " + addr)

    if len(new_addrs) == 0:
        new_addrs.append(("127.0.0.1", "6379"))

    redis_kwargs["addrs"] = new_addrs

    pool_kwargs = {
        "max_connections": pool_kwargs.get("max_connections", max_connections),
        "timeout": pool_kwargs.get("timeout", (redis_kwargs.get("socket_timeout") or 3) + 1),
    }

    tls_kwargs.update(
        {
            "ssl_keyfile": None,
            "ssl_certfile": None,
            "ssl_cert_reqs": "required",
            "ssl_ca_certs": None,
            "ssl_ca_data": None,
            "ssl_ca_path": None,
            "ssl_check_hostname": False,
            "ssl_password": None,
            "ssl_validate_ocsp": False,
            "ssl_validate_ocsp_stapled": False,
            "ssl_ocsp_context": None,
            "ssl_ocsp_expected_cert": None,
        }
    )

    return pool_kwargs, redis_kwargs, tls_kwargs


def process_config(url, pool_kwargs, redis_kwargs, tls_kwargs):
    config = {}

    addrs = redis_kwargs.pop("addrs")
    cluster_error_retry_attempts = redis_kwargs.pop("cluster_error_retry_attempts")
    service_name = redis_kwargs.pop("service_name") if "service_name" in redis_kwargs else None
    sentinel_username = (
        redis_kwargs.pop("sentinel_username") if "sentinel_username" in redis_kwargs else None
    )
    sentinel_password = (
        redis_kwargs.pop("sentinel_password") if "sentinel_password" in redis_kwargs else None
    )
    scheme_parts = url.scheme.split("+")

    if scheme_parts[0] == "rediss":
        config["tls"] = True
        redis_kwargs |= tls_kwargs

    if len(scheme_parts) > 1:
        match scheme_parts[1]:
            case "sentinel" | "sentinels":
                if not service_name:
                    raise ValueError("For sentinel usage a mastername has to be specified!")
                # Update username / password for sentinel connection
                sentinel_kwargs = deepcopy(redis_kwargs)
                if sentinel_username:
                    sentinel_kwargs["username"] = sentinel_username
                elif "username" in sentinel_kwargs:
                    sentinel_kwargs.pop("username")
                if sentinel_password:
                    sentinel_kwargs["password"] = sentinel_password
                elif "password" in sentinel_kwargs:
                    sentinel_kwargs.pop("password")
                # Remove any unneeded host / port configuration
                if "host" in redis_kwargs:
                    redis_kwargs.pop("host")
                if "port" in redis_kwargs:
                    redis_kwargs.pop("port")
                config["type"] = "sentinel"
                config["pool_kwargs"] = deepcopy(pool_kwargs)
                config["redis_kwargs"] = deepcopy(redis_kwargs)
                config["service_name"] = service_name
                config["sentinels"] = []
                # Manually override sentinels in order to use BlockingConnectionPool
                for hostname, port in addrs:
                    sentinel_kwargs["host"] = hostname
                    sentinel_kwargs["port"] = port
                    config["sentinels"] += [deepcopy(sentinel_kwargs)]
            case "cluster" | "clusters":
                config["type"] = "cluster"
                config["pool_kwargs"] = deepcopy(pool_kwargs)
                config["redis_kwargs"] = deepcopy(redis_kwargs)
                config["addrs"] = addrs
                config["cluster_error_retry_attempts"] = cluster_error_retry_attempts
            case "socket":
                if scheme_parts[0] == "rediss":
                    raise ValueError("Redis unix socket connection does not support SSL!")
                redis_kwargs["path"] = (addrs[0][0] + ":" + str(addrs[0][1]), url.path)
                config["type"] = "socket"
                config["pool_kwargs"] = deepcopy(pool_kwargs)
                config["redis_kwargs"] = deepcopy(redis_kwargs)
            case _:
                raise ValueError("Unknown scheme found in redis connection URL: " + url.scheme)

    if scheme_parts[0] != "redis" and scheme_parts[0] != "rediss":
        raise ValueError("Unknown scheme found in redis connection URL: " + url.scheme)

    if "type" not in config:
        redis_kwargs["host"] = addrs[0][0]
        redis_kwargs["port"] = addrs[0][1]
        config["type"] = "default"
        config["pool_kwargs"] = deepcopy(pool_kwargs)
        config["redis_kwargs"] = deepcopy(redis_kwargs)

    return config


def get_connection_pool(config, use_async=False, update_connection_class=None):
    connection_pool = None
    client_config = {}
    config = deepcopy(config)

    connection_pool_class = AsyncBlockingConnectionPool if use_async else BlockingConnectionPool
    redis_class = AsyncStrictRedis if use_async else StrictRedis
    redis_cluster_class = AsyncRedisCluster if use_async else RedisCluster
    sentinel_class = AsyncSentinel if use_async else Sentinel
    sentinel_connection_pool_class = (
        AsyncSentinelConnectionPool if use_async else SentinelConnectionPool
    )
    cluster_node_class = AsyncClusterNode if use_async else ClusterNode
    retry_class = AsyncRetry if use_async else Retry
    unix_domain_socket_connection_class = (
        AsyncUnixDomainSocketConnection if use_async else UnixDomainSocketConnection
    )

    if config.get("tls", False):
        if use_async:
            redis_connection_class = AsyncSSLConnection
            sentinel_managed_connection_class = AsyncSentinelManagedSSLConnection
        else:
            redis_connection_class = SSLConnection
            sentinel_managed_connection_class = SentinelManagedSSLConnection
    else:
        if use_async:
            redis_connection_class = AsyncConnection
            sentinel_managed_connection_class = AsyncSentinelManagedConnection
        else:
            redis_connection_class = Connection
            sentinel_managed_connection_class = SentinelManagedConnection
    if callable(update_connection_class):
        redis_connection_class = update_connection_class(redis_connection_class)
    config["redis_kwargs"]["connection_class"] = redis_connection_class

    retries_and_backoff = config["redis_kwargs"].pop("retry")
    if "retry" in retries_and_backoff:
        if "min_backoff" in retries_and_backoff and "max_backoff" in retries_and_backoff:
            config["redis_kwargs"]["retry"] = retry_class(
                ExponentialBackoff(
                    retries_and_backoff["max_backoff"], retries_and_backoff["min_backoff"]
                ),
                retries_and_backoff["retry"],
            )
        elif "min_backoff" in retries_and_backoff:
            config["redis_kwargs"]["retry"] = retry_class(
                ConstantBackoff(retries_and_backoff["min_backoff"]), retries_and_backoff["retry"]
            )
        elif "max_backoff" in retries_and_backoff:
            config["redis_kwargs"]["retry"] = retry_class(
                ConstantBackoff(retries_and_backoff["max_backoff"]), retries_and_backoff["retry"]
            )
        else:
            config["redis_kwargs"]["retry"] = retry_class(NoBackoff(), retries_and_backoff["retry"])

    config["redis_kwargs"].setdefault(
        "retry", retry_class(ExponentialBackoff(DEFAULT_CAP, DEFAULT_BASE), 3)
    )
    config["redis_kwargs"].setdefault(
        "retry_on_error", [ConnectionError, TimeoutError, SocketTimeout]
    )

    match config["type"]:
        case "sentinel":
            redis_connection_class = config["redis_kwargs"].pop("connection_class")
            if callable(update_connection_class):
                sentinel_managed_connection_class = update_connection_class(
                    sentinel_managed_connection_class
                )
            config["redis_kwargs"]["connection_class"] = sentinel_managed_connection_class
            sentinel = sentinel_class(sentinels=[], **config["redis_kwargs"])
            for sentinel_config in config["sentinels"]:
                sentinel_config["retry"] = config["redis_kwargs"]["retry"]
                sentinel_config["connection_class"] = redis_connection_class
                connection_pool = connection_pool_class(**config["pool_kwargs"], **sentinel_config)
                sentinel_client = redis_class(connection_pool=connection_pool)
                if config["redis_kwargs"].get("readonly", False):
                    sentinel_client.readonly()
                sentinel.sentinels.append(sentinel_client)
            pool_kwargs = sentinel.connection_kwargs
            pool_kwargs |= {"is_master": not config.get("is_slave", False)}
            connection_pool = sentinel_connection_pool_class(
                config["service_name"], sentinel, **pool_kwargs
            )
            client_config["client_class"] = redis_class
        case "cluster":
            connection_pool = connection_pool_class(
                **config["pool_kwargs"], **config["redis_kwargs"]
            )
            client_config["client_kwargs"] = {
                "startup_nodes": [cluster_node_class(*node) for node in config["addrs"]],
                "cluster_error_retry_attempts": config["cluster_error_retry_attempts"],
                "skip_full_coverage_check": True,
            }
            client_config["client_class"] = redis_cluster_class
        case "socket":
            if callable(update_connection_class):
                config["redis_kwargs"]["connection_class"] = update_connection_class(
                    unix_domain_socket_connection_class
                )
            else:
                config["redis_kwargs"]["connection_class"] = unix_domain_socket_connection_class
            connection_pool = connection_pool_class(
                **config["pool_kwargs"], **config["redis_kwargs"]
            )
            client_config["client_class"] = redis_class
        case "default":
            connection_pool = connection_pool_class(
                **config["pool_kwargs"], **config["redis_kwargs"]
            )
            client_config["client_class"] = redis_class

    if config["redis_kwargs"].get("readonly", False):
        client_config["readonly"] = True

    return connection_pool, client_config


def get_client(client_config, connection_pool=None):
    if connection_pool is not None:
        client_config.setdefault("client_kwargs", {})["connection_pool"] = connection_pool
    client = client_config["client_class"](**client_config["client_kwargs"])
    if client_config.get("readonly", False):
        client.readyonly()
    return client


def parse_url(url):
    url = urlparse(url)
    config = process_config(url, *get_redis_options(url))
    pool, client_config = get_connection_pool(config)

    return get_client(client_config, pool)
