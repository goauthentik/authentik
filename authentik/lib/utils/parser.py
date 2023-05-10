"""redis URL parser"""
from asyncio import PriorityQueue
from copy import deepcopy
from socket import TCP_KEEPCNT, TCP_KEEPINTVL
from socket import timeout as SocketTimeout
from sys import platform
from typing import Any, Dict, Tuple
from urllib.parse import ParseResultBytes, parse_qs, unquote, unquote_plus, urlparse

from django.utils.module_loading import import_string
from redis.backoff import DEFAULT_BASE, DEFAULT_CAP, ConstantBackoff, ExponentialBackoff, NoBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

FALSE_STRINGS = ("0", "F", "FALSE", "N", "NO")


def _to_bool(value):
    """Convert string to bool"""
    match value:
        case "1" | "t" | "T" | "true" | "TRUE" | "True":
            return True
        case "0" | "f" | "F" | "false" | "FALSE" | "False":
            return False
    print("Invalid boolean value found in Redis URL query, skipping")
    return False


def _parse_duration_to_sec(duration_str: str) -> float:
    """This function parses a duration string into a float of seconds.

    It supports the following units: ns, us, ms, s, m, h.
    It returns a ValueError if the string is invalid or empty.
    """
    if not duration_str:
        raise ValueError("empty string")
    units = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}
    result = 0.0
    num = ""
    for duration_char in duration_str:
        if duration_char.isdigit() or duration_char == ".":
            num += duration_char
        elif duration_char.isalpha():
            if num == "":
                raise ValueError("invalid format")
            unit = duration_char
            while unit not in units:
                if len(unit) == 2:
                    raise ValueError("unknown unit")
                unit = duration_char + duration_str[duration_str.index(duration_char) + 1]
            result += float(num) * units[unit]
            num = ""
        else:
            raise ValueError("invalid character")
    if num != "":
        raise ValueError("missing unit")
    return result


def _val_to_sec(values: list[bytes]):
    """Convert a list of string bytes into a duration in seconds"""
    result = None
    for value in values:
        try:
            result = _parse_duration_to_sec(str(value))
            return result
        except ValueError:
            result = int(value)
    return result


def parse_hostport(addr_str, default_port=6379):
    """Convert string into host port"""
    if addr_str[-1] == "]":
        # ipv6 literal (with no port)
        return addr_str, default_port

    out = addr_str.rsplit(":", 1)
    if len(out) == 1:
        # No port
        port = default_port
    else:
        try:
            port = int(out[1])
        except ValueError:
            raise ValueError("Invalid host:port '%s'" % addr_str)

    return out[0], port


def _configure_tcp_keepalive(kwargs):
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


def _set_kwargs_default(kwargs: dict, defaults: dict):
    """Set multiple default values for a dictionary at once"""
    for kwarg_key, kwarg_value in defaults.items():
        kwargs.setdefault(kwarg_key, kwarg_value)
    return kwargs


def get_addrs_from_url(url):
    """Extract Redis addresses from configuration URL"""
    if url.hostname:
        host = unquote_plus(url.netloc).split("@")
        if len(host) > 1:
            host = host[-1]
        else:
            host = host[0]
        return host.split(",")
    return []


def _set_config_defaults(pool_kwargs, redis_kwargs, tls_kwargs, url):
    """Update config with default values"""
    redis_kwargs.setdefault("addrs", []).extend(get_addrs_from_url(url))

    if url.path and url.scheme != "redis+socket":
        path = unquote(url.path)[1:]
        if path.isdigit():
            redis_kwargs["db"] = int(path)

    try:
        # Retrieve the number of cpus that can be used
        from os import sched_getaffinity

        max_connections = len(sched_getaffinity(0)) * 10
    except (ImportError, AttributeError):
        # Use default value of BlockingConnectionPool
        max_connections = 50

    new_addrs = []
    default_port = 26379 if "sentinel" in str(url.scheme) else 6379
    for addr in redis_kwargs.pop("addrs", []):
        try:
            new_addrs.append(parse_hostport(addr, default_port))
        except ValueError:
            print("Skipping due to invalid format for a hostname and port: " + addr)

    if len(new_addrs) == 0:
        new_addrs.append(("127.0.0.1", "6379"))

    pool_kwargs_defaults = {
        "max_connections": max_connections,
        "timeout": (redis_kwargs.get("socket_timeout") or 3) + 1,
    }

    redis_kwargs_defaults = {
        "addrs": new_addrs,
        "cluster_error_retry_attempts": 3,
        "socket_connect_timeout": 5,
        "socket_timeout": 3,
    }

    tls_kwargs_defaults = {
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

    pool_kwargs = _set_kwargs_default(pool_kwargs, pool_kwargs_defaults)
    redis_kwargs = _set_kwargs_default(redis_kwargs, redis_kwargs_defaults)
    tls_kwargs = _set_kwargs_default(tls_kwargs, tls_kwargs_defaults)

    return pool_kwargs, redis_kwargs, tls_kwargs


def get_credentials_from_url(redis_kwargs, url):
    """Extract username and password from URL"""
    if url.password:
        redis_kwargs["password"] = url.password
        if url.username:
            redis_kwargs["username"] = url.username
    elif url.username:
        if url.netloc.split("@")[0][-1] == ":":
            redis_kwargs["username"] = url.username
        else:
            redis_kwargs["password"] = url.username
    return redis_kwargs


# pylint: disable=too-many-locals, too-many-statements
def get_redis_options(
    url: ParseResultBytes, disable_socket_timeout=False
) -> Tuple[Dict, Dict, Dict]:
    """Converts a parsed url into necessary dicts to create a redis client"""
    pool_kwargs = {}
    redis_kwargs = {}
    tls_kwargs = {}

    retries_and_backoff = {}

    redis_kwargs = get_credentials_from_url(redis_kwargs, url)

    for name, value in parse_qs(url.query).items():
        if value and len(value) > 0 and isinstance(name, str):
            value_str = value[0]
            match name.lower():
                case "addr":
                    redis_kwargs.setdefault("addrs", []).extend([addr for addr in value])
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
                    min_backoff = _val_to_sec(value)
                    if min_backoff is not None and min_backoff > 0:
                        retries_and_backoff["min_backoff"] = min_backoff
                case "maxretrybackoff":
                    max_backoff = _val_to_sec(value)
                    if max_backoff is not None and max_backoff > 0:
                        retries_and_backoff["max_backoff"] = max_backoff
                case "timeout":
                    timeout = _val_to_sec(value)
                    if timeout is not None and timeout <= 0:
                        timeout = None
                    if "socket_connect_timeout" not in redis_kwargs:
                        redis_kwargs["socket_connect_timeout"] = timeout
                    if "socket_timeout" not in redis_kwargs:
                        redis_kwargs["socket_timeout"] = timeout
                case "dialtimeout":
                    socket_connect_timeout = _val_to_sec(value)
                    if socket_connect_timeout is not None and socket_connect_timeout <= 0:
                        socket_connect_timeout = None
                    redis_kwargs["socket_connect_timeout"] = socket_connect_timeout
                case "readtimeout" | "writetimeout":
                    socket_timeout = _val_to_sec(value)
                    if socket_timeout is not None and socket_timeout <= 0:
                        socket_timeout = None
                    if (
                        "socket_timeout" not in redis_kwargs
                        or redis_kwargs.get("socket_timeout") < socket_timeout
                    ):
                        redis_kwargs["socket_timeout"] = socket_timeout
                case "poolfifo":
                    if _to_bool(value[0]):
                        pool_kwargs["queue_class"] = PriorityQueue
                case "poolsize":
                    pool_kwargs["max_connections"] = int(value[0])
                case "pooltimeout":
                    pool_timeout = _val_to_sec(value)
                    if pool_timeout is not None and pool_timeout <= 0:
                        pool_timeout = None
                    pool_kwargs["timeout"] = pool_timeout
                case "idletimeout":
                    redis_kwargs["idle_timeout"] = int(_val_to_sec(value))
                case "idlecheckfrequency":
                    redis_kwargs["idle_check_frequency"] = int(_val_to_sec(value))
                case "maxidleconns":
                    redis_kwargs["max_connections"] = int(value[0])
                case "sentinelmasterid" | "mastername":
                    redis_kwargs["service_name"] = value_str
                case "sentinelusername":
                    redis_kwargs["sentinel_username"] = value_str
                case "sentinelpassword":
                    redis_kwargs["sentinel_password"] = value_str
                case "readonly":
                    redis_kwargs["readonly"] = _to_bool(value_str)
                case "skipverify":
                    # Always let most radical option take precedence
                    # The Go implementation always uses ssl_cert_reqs = "none"
                    if _to_bool(value_str) and tls_kwargs.get("ssl_cert_reqs") != "none":
                        tls_kwargs["ssl_cert_reqs"] = "optional"
                case "insecureskipverify":
                    if _to_bool(value_str):
                        tls_kwargs["ssl_cert_reqs"] = "none"
                case "minidleconns" | "maxredirects" | "routebylatency" | "routerandomly":
                    print(
                        'The configuration option "'
                        + name.lower()
                        + '" is currently not supported by the Python'
                        + " redis implementation and therefore ignored."
                    )
                case _:
                    raise ValueError(
                        'Detected unknown configuration option "'
                        + name.lower()
                        + '"! Please check your configuration.'
                    )

    redis_kwargs["retry"] = retries_and_backoff

    if disable_socket_timeout:
        redis_kwargs["socket_timeout"] = None

    redis_kwargs = _configure_tcp_keepalive(redis_kwargs)

    return _set_config_defaults(pool_kwargs, redis_kwargs, tls_kwargs, url)


def _config_sentinel(config, service_name, credentials, kwargs, addrs):
    """Configure options for Redis sentinel"""
    if not service_name:
        raise ValueError("For sentinel usage a mastername has to be specified!")
    sentinel_username, sentinel_password = credentials
    redis_kwargs, pool_kwargs = kwargs
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
    return config


def process_config(url, pool_kwargs, redis_kwargs, tls_kwargs):
    """Creates one dict that holds necessary config to create redis client"""
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
                credentials = (sentinel_username, sentinel_password)
                kwargs = (redis_kwargs, pool_kwargs)
                config = _config_sentinel(config, service_name, credentials, kwargs, addrs)
            case "cluster" | "clusters":
                config["type"] = "cluster"
                database = redis_kwargs.pop("db")
                if database:
                    print("Redis cluster does not support the db option, skipping")
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


def _connection_class(config, use_async, update_connection_class):
    if config["type"] != "cluster":
        redis_connection_class_path = "connection."
        sentinel_managed_connection_class_path = "sentinel.SentinelManaged"
        if config.get("tls", False):
            redis_connection_class_path += "SSL"
            sentinel_managed_connection_class_path += "SSL"
        redis_connection_class_path += "Connection"
        redis_connection_class = _get_class(redis_connection_class_path, use_async)
        sentinel_managed_connection_class_path += "Connection"
        sentinel_managed_connection_class = _get_class(
            sentinel_managed_connection_class_path, use_async
        )
        if callable(update_connection_class):
            redis_connection_class = update_connection_class(redis_connection_class)
        config["redis_kwargs"]["connection_class"] = redis_connection_class

        if config["type"] == "sentinel":
            if callable(update_connection_class):
                sentinel_managed_connection_class = update_connection_class(
                    sentinel_managed_connection_class
                )
            config["redis_kwargs"]["connection_class"] = sentinel_managed_connection_class
    return config


def _retries_and_backoff(config, retry_class):
    """Configure retry and backoff similar to how go-redis handles it"""
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
        "retry_on_error", [RedisConnectionError, RedisTimeoutError, SocketTimeout]
    )
    return config


def _get_class(class_path, use_async=False) -> Any:
    module_path = "redis."
    if use_async:
        module_path += "asyncio."
    module_path += class_path
    return import_string(module_path)


def get_connection_pool(config, use_async=False, update_connection_class=None):
    """Returns a connection pool given a valid redis configuration dict"""
    connection_pool = None
    client_config = {}
    config = deepcopy(config)

    config = _connection_class(config, use_async, update_connection_class)
    config = _retries_and_backoff(config, _get_class("retry.Retry", use_async))

    match config["type"]:
        case "sentinel":
            redis_connection_class = config["redis_kwargs"].pop("connection_class")
            sentinel = _get_class("sentinel.Sentinel", use_async)(
                sentinels=[], **config["redis_kwargs"]
            )
            for sentinel_config in config["sentinels"]:
                sentinel_config["retry"] = config["redis_kwargs"]["retry"]
                sentinel_config["connection_class"] = redis_connection_class
                connection_pool = _get_class("connection.BlockingConnectionPool", use_async)(
                    **config["pool_kwargs"], **sentinel_config
                )
                sentinel_client = _get_class("client.StrictRedis", use_async)(
                    connection_pool=connection_pool
                )
                sentinel.sentinels.append(sentinel_client)
            pool_kwargs = sentinel.connection_kwargs
            pool_kwargs |= {"is_master": not config.get("is_slave", False)}
            connection_pool = _get_class("sentinel.SentinelConnectionPool", use_async)(
                config["service_name"], sentinel, **pool_kwargs
            )
            client_config["client_class"] = _get_class("client.StrictRedis", use_async)
        case "cluster":
            client_config["client_kwargs"] = {
                "startup_nodes": [
                    _get_class("cluster.ClusterNode", use_async)(*node) for node in config["addrs"]
                ],
                "cluster_error_retry_attempts": config["cluster_error_retry_attempts"],
                "read_from_replicas": config["redis_kwargs"].get("readonly", False),
                **config["redis_kwargs"],
            }
            client_config["client_class"] = _get_class("cluster.RedisCluster", use_async)
        case "socket":
            if callable(update_connection_class):
                config["redis_kwargs"]["connection_class"] = update_connection_class(
                    _get_class("connection.UnixDomainSocketConnection", use_async)
                )
            else:
                config["redis_kwargs"]["connection_class"] = _get_class(
                    "connection.UnixDomainSocketConnection", use_async
                )
            connection_pool = _get_class("connection.BlockingConnectionPool", use_async)(
                **config["pool_kwargs"], **config["redis_kwargs"]
            )
            client_config["client_class"] = _get_class("client.StrictRedis", use_async)
        case "default":
            connection_pool = _get_class("connection.BlockingConnectionPool", use_async)(
                **config["pool_kwargs"], **config["redis_kwargs"]
            )
            client_config["client_class"] = _get_class("client.StrictRedis", use_async)

    return connection_pool, client_config


def get_client(client_config, connection_pool=None):
    """Get a redis client using a valid redis config dict and a connection pool"""
    if connection_pool is not None:
        client_config.setdefault("client_kwargs", {})["connection_pool"] = connection_pool
    client = client_config["client_class"](**client_config["client_kwargs"])
    return client


def parse_url(url):
    """Parse a redis configuration URL and return a redis client"""
    url = urlparse(url)
    config = process_config(url, *get_redis_options(url))
    pool, client_config = get_connection_pool(config)

    return get_client(client_config, pool)
