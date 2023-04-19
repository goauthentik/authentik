import os
from asyncio import PriorityQueue, LifoQueue
from socket import timeout as SocketTimeout
from typing import Tuple, Dict
from urllib.parse import parse_qs, unquote, urlparse, ParseResultBytes

from redis.asyncio.client import StrictRedis as AsyncStrictRedis
from redis.asyncio.connection import SSLConnection as AsyncSSLConnection
from redis.asyncio.connection import UnixDomainSocketConnection as AsyncUnixDomainSocketConnection
from redis.asyncio.retry import Retry as AsyncRetry
from redis.asyncio.connection import BlockingConnectionPool as AsyncBlockingConnectionPool
from redis.asyncio.cluster import RedisCluster as AsyncRedisCluster
from redis.asyncio.cluster import ClusterNode as AsyncClusterNode
from redis.asyncio.sentinel import Sentinel as AsyncSentinel
from redis.backoff import NoBackoff, ExponentialBackoff, ConstantBackoff
from redis.client import StrictRedis
from redis.cluster import ClusterNode, RedisCluster
from redis.connection import SSLConnection, UnixDomainSocketConnection, BlockingConnectionPool
from redis.retry import Retry
from redis.sentinel import Sentinel

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
    if s[-1] == ']':
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


# TODO: Check which errors are retried in go-redis
def get_redis_options(url: ParseResultBytes, use_async=False) -> Tuple[Dict, Dict, Dict]:
    pool_kwargs = {}
    redis_kwargs = {}
    tls_kwargs = {}

    retries_and_backoff = {}
    retry_class = AsyncRetry if use_async else Retry

    if url.password:
        redis_kwargs["password"] = unquote(url.password)
        if url.username:
            redis_kwargs["username"] = unquote(url.username)
    elif url.username:
        redis_kwargs["password"] = unquote(url.username)

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
                    if "socket_timeout" not in redis_kwargs or redis_kwargs.get("socket_timeout") < socket_timeout:
                        redis_kwargs["socket_timeout"] = socket_timeout
                case "poolfifo":
                    if to_bool(value[0]):
                        pool_kwargs["queue_class"] = PriorityQueue
                    else:
                        pool_kwargs["queue_class"] = LifoQueue
                case "poolsize":
                    pool_kwargs["max_connections"] = int(value[0])
                case "pooltimeout":
                    pool_kwargs["timeout"] = val_to_sec(value)
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
                case "minidleconns" | "maxredirects" | "routebylatency" | "routerandomly" | "writetimeout":
                    # Replace with internal logging of authentik!
                    print(
                        "The configuration option \"" + name.lower() + "\" is currently not supported by the Python redis implementation and thereby ignored.")
                case _:
                    # Replace with internal logging of authentik!
                    raise ValueError(
                        "Detected unknown configuration option \"" + name.lower() + "\"! Please check your configuration.")

    if "retry" in retries_and_backoff:
        if "min_backoff" in retries_and_backoff and "max_backoff" in retries_and_backoff:
            redis_kwargs["retry"] = retry_class(
                ExponentialBackoff(
                    retries_and_backoff["max_backoff"],
                    retries_and_backoff["min_backoff"]
                ),
                retries_and_backoff["retry"]
            )
        elif "min_backoff" in retries_and_backoff:
            redis_kwargs["retry"] = retry_class(
                ConstantBackoff(retries_and_backoff["min_backoff"]),
                retries_and_backoff["retry"]
            )
        elif "max_backoff" in retries_and_backoff:
            redis_kwargs["retry"] = retry_class(
                ConstantBackoff(retries_and_backoff["max_backoff"]),
                retries_and_backoff["retry"]
            )
        else:
            redis_kwargs["retry"] = retry_class(
                NoBackoff(),
                retries_and_backoff["retry"]
            )

    redis_kwargs.setdefault("cluster_error_retry_attempts", 3)
    redis_kwargs.setdefault("retry", retry_class(ExponentialBackoff(), 3))
    redis_kwargs.setdefault("retry_on_error", (ConnectionError, TimeoutError, SocketTimeout))
    redis_kwargs.setdefault("socket_connect_timeout", 3)
    redis_kwargs.setdefault("socket_timeout", 3)

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
        max_connections = len(os.sched_getaffinity(0)) * 10
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
        "timeout": pool_kwargs.get("timeout", redis_kwargs["socket_timeout"] + 1)
    }

    tls_kwargs.update(
        {
            "connection_class": AsyncSSLConnection if use_async else SSLConnection,
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


def process_config(url, pool_kwargs, redis_kwargs, tls_kwargs, use_async=False):
    config = {}

    addrs = redis_kwargs.pop("addrs")
    cluster_error_retry_attempts = redis_kwargs.pop("cluster_error_retry_attempts")
    service_name = redis_kwargs.pop("service_name") if "service_name" in redis_kwargs else None
    sentinel_username = redis_kwargs.pop("sentinel_username") if "sentinel_username" in redis_kwargs else None
    sentinel_password = redis_kwargs.pop("sentinel_password") if "sentinel_password" in redis_kwargs else None
    scheme_parts = url.scheme.split("+")

    if scheme_parts[0] == "rediss":
        redis_kwargs |= tls_kwargs

    if len(scheme_parts) > 1:
        match scheme_parts[1]:
            case "sentinel" | "sentinels":
                if not service_name:
                    raise ValueError("For sentinel usage a mastername has to be specified!")
                # Update username / password for sentinel connection
                sentinel_kwargs = redis_kwargs.copy()
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
                config["pool_kwargs"] = pool_kwargs.copy()
                config["sentinel_kwargs"] = sentinel_kwargs.copy()
                config["redis_kwargs"] = redis_kwargs.copy()
                config["service_name"] = service_name
                config["sentinels"] = []
                # Manually override sentinels in order to use BlockingConnectionPool
                for hostname, port in addrs:
                    redis_kwargs["host"] = hostname
                    redis_kwargs["port"] = port
                    config["sentinels"] += [redis_kwargs.copy()]
            case "cluster" | "clusters":
                config["type"] = "cluster"
                config["pool_kwargs"] = pool_kwargs.copy()
                config["redis_kwargs"] = redis_kwargs.copy()
                config["addrs"] = addrs
                config["cluster_error_retry_attempts"] = cluster_error_retry_attempts
            case "socket":
                if scheme_parts[0] == "rediss":
                    raise ValueError("Redis unix socket connection does not support SSL!")
                redis_kwargs["connection_class"] = AsyncUnixDomainSocketConnection if use_async else UnixDomainSocketConnection
                redis_kwargs["path"] = (addrs[0][0] + ":" + str(addrs[0][1]), url.path)
                config["type"] = "socket"
                config["pool_kwargs"] = pool_kwargs.copy()
                config["redis_kwargs"] = redis_kwargs.copy()
            case _:
                raise ValueError("Unknown scheme found in redis connection URL: " + url.scheme)

    if scheme_parts[0] != "redis" and scheme_parts[0] != "rediss":
        raise ValueError("Unknown scheme found in redis connection URL: " + url.scheme)

    if "type" not in config:
        redis_kwargs["host"] = addrs[0][0]
        redis_kwargs["port"] = addrs[0][1]
        config["type"] = "default"
        config["pool_kwargs"] = pool_kwargs.copy()
        config["redis_kwargs"] = redis_kwargs.copy()

    return config


def get_client(config, use_async=False):
    client = None

    connection_pool_class = AsyncBlockingConnectionPool if use_async else BlockingConnectionPool
    redis_class = AsyncStrictRedis if use_async else StrictRedis
    redis_cluster_class = AsyncRedisCluster if use_async else RedisCluster
    sentinel_class = AsyncSentinel if use_async else Sentinel
    cluster_node_class = AsyncClusterNode if use_async else ClusterNode

    match config["type"]:
        case "sentinel":
            sentinel = sentinel_class(sentinels=[], sentinel_kwargs=config["sentinel_kwargs"], **config["redis_kwargs"])
            for sentinel_config in config["sentinels"]:
                connection_pool = connection_pool_class(**config["pool_kwargs"], **sentinel_config)
                sentinel_client = redis_class(connection_pool=connection_pool)
                if config["redis_kwargs"].get("readonly", False):
                    sentinel_client.readonly()
                sentinel.sentinels.append(sentinel_client)
            client = sentinel.master_for(service_name=config["service_name"], redis_class=StrictRedis)
            if config.get("is_slave", False):
                client = sentinel.slave_for(service_name=config["service_name"], redis_class=StrictRedis)
        case "cluster":
            connection_pool = connection_pool_class(**config["pool_kwargs"], **config["redis_kwargs"])
            client = redis_cluster_class(
                startup_nodes=[cluster_node_class(*node) for node in config["addrs"]],
                cluster_error_retry_attempts=config["cluster_error_retry_attempts"],
                connection_pool=connection_pool
            )
        case "socket":
            connection_pool = connection_pool_class(**config["pool_kwargs"], **config["redis_kwargs"])
            client = redis_class(connection_pool=connection_pool)
        case "default":
            connection_pool = connection_pool_class(**config["pool_kwargs"], **config["redis_kwargs"])
            client = redis_class(connection_pool=connection_pool)

    if config["redis_kwargs"].get("readonly", False):
        client.readonly()

    return client


def parse_url(url):
    url = urlparse(url)
    config = process_config(url, *get_redis_options(url))

    return get_client(config)
