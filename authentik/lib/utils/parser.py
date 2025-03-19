"""redis URL parser"""

from asyncio import PriorityQueue
from copy import deepcopy
from random import shuffle
from socket import TCP_KEEPCNT, TCP_KEEPINTVL
from socket import timeout as SocketTimeout
from sys import platform
from typing import Any
from urllib.parse import ParseResultBytes, parse_qs, unquote, unquote_plus, urlparse

from django.utils.module_loading import import_string
from redis.backoff import DEFAULT_BASE, DEFAULT_CAP, FullJitterBackoff
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

DEFAULT_RETRIES = 3


class SETDEFAULT:
    """Used to indicate that value shall be overridden by default"""


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
    units = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}
    result = 0.0
    num = ""
    negative = False
    skip_loop = False
    for i, duration_char in enumerate(duration_str):
        if skip_loop:
            skip_loop = False
            continue
        if duration_char.isdigit() or duration_char == ".":
            num += duration_char
        elif duration_char == "-":
            negative = True
        elif duration_char.isalpha():
            if num == "":
                raise ValueError("invalid format")
            unit = duration_char
            if len(duration_str) == i + 2:
                if duration_str[i + 1].isalpha():
                    unit += duration_str[i + 1]
                    skip_loop = True
            if unit not in units:
                raise ValueError("unknown unit")
            result += float(num) * units[unit]
            num = ""
        else:
            raise ValueError("invalid character")
    if num != "":
        raise ValueError("missing unit")
    if negative:
        result *= -1
    return result


def _val_to_sec(values: list[bytes]):
    """Convert a list of string bytes into a duration in seconds"""
    for value in values:
        try:
            return int(value)
        except ValueError:
            try:
                return _parse_duration_to_sec(str(value))
            except ValueError:
                continue
    return 0


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
        except ValueError as err:
            raise ValueError(f"Invalid host:port '{addr_str}'") from err

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
    idle_check_frequency = kwargs.pop("idle_check_frequency", None)
    idle_check_frequency = idle_check_frequency if idle_check_frequency is not None else 60
    idle_timeout = kwargs.pop("idle_timeout", None)
    idle_timeout = idle_timeout if idle_timeout is not None else 5 * 60
    kwargs.setdefault(
        "socket_keepalive_options",
        {
            activate_keepalive_sec: 5 * 60,
            TCP_KEEPINTVL: idle_check_frequency,
            TCP_KEEPCNT: idle_timeout // idle_check_frequency,
        },
    )

    return kwargs


def _set_kwargs_default(kwargs: dict, defaults: dict):
    """Set multiple default values for a dictionary at once"""
    for kwarg_key, kwarg_value in defaults.items():
        kwargs.setdefault(kwarg_key, kwarg_value)
        if kwargs.get(kwarg_key) is SETDEFAULT:
            kwargs[kwarg_key] = kwarg_value
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
        new_addrs.append(("127.0.0.1", default_port))

    pool_socket_timeout = redis_kwargs.get("socket_timeout")
    if pool_socket_timeout is None or pool_socket_timeout is SETDEFAULT:
        pool_socket_timeout = 3

    pool_kwargs_defaults = {
        "max_connections": max_connections,
        "timeout": pool_socket_timeout + 1,
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


def _handle_default(
    value, condition=lambda x: x is not None and x > 0, default=0, handle_zero=True
):
    """Handle any not supported values i.e. negative ones"""
    if condition(value):
        return value
    if handle_zero and value == 0:
        return SETDEFAULT
    return default


# pylint: disable=too-many-locals, too-many-statements
def get_redis_options(
    url: ParseResultBytes, disable_socket_timeout=False
) -> tuple[dict, dict, dict]:
    """Converts a parsed url into necessary dicts to create a redis client"""
    pool_kwargs = {}
    redis_kwargs = {}
    tls_kwargs = {}

    retries_and_backoff = {}

    redis_kwargs = get_credentials_from_url(redis_kwargs, url)

    for name, value in parse_qs(url.query, keep_blank_values=True).items():
        if value and isinstance(name, str):
            value_str = value[0]
            match name.lower():
                case "addr":
                    redis_kwargs.setdefault("addrs", []).extend(value)
                case "addrs":
                    redis_kwargs.setdefault("addrs", []).extend(value_str.split(","))
                case "username":
                    redis_kwargs["username"] = value_str
                case "password":
                    redis_kwargs["password"] = value_str
                case "database" | "db":
                    redis_kwargs["db"] = _handle_default(int(value[0]), handle_zero=False)
                case "maxretries":
                    # Negative values for maxretries are handled differently
                    # in Golang and Python.
                    # Golang: Negative retries lead to no attempt -> failure
                    # Python: Negative retries lead to infinite attempts
                    # Therefore we do not allow them at all -> set to 0
                    retry = int(value[0])
                    retries_and_backoff["retry"] = _handle_default(retry)
                    redis_kwargs["cluster_error_retry_attempts"] = _handle_default(retry)
                case "minretrybackoff":
                    retries_and_backoff["min_backoff"] = _handle_default(_val_to_sec(value))
                case "maxretrybackoff":
                    retries_and_backoff["max_backoff"] = _handle_default(_val_to_sec(value))
                case "timeout":
                    timeout = _val_to_sec(value)
                    redis_kwargs.setdefault(
                        "socket_connect_timeout",
                        _handle_default(timeout),
                    )
                    redis_kwargs.setdefault("socket_timeout", _handle_default(timeout))
                case "dialtimeout":
                    redis_kwargs["socket_connect_timeout"] = _handle_default(_val_to_sec(value))
                case "readtimeout" | "writetimeout":
                    redis_kwargs["socket_timeout"] = _handle_default(
                        _val_to_sec(value),
                        condition=lambda x: x > redis_kwargs.get("socket_timeout", 0),
                        default=redis_kwargs.get("socket_timeout"),
                    )
                case "poolfifo":
                    if _to_bool(value[0]):
                        pool_kwargs["queue_class"] = PriorityQueue
                case "poolsize":
                    pool_kwargs["max_connections"] = _handle_default(
                        int(value[0]), condition=lambda x: x >= 1, default=1
                    )
                case "pooltimeout":
                    pool_kwargs["timeout"] = _handle_default(_val_to_sec(value))
                case "idletimeout":
                    redis_kwargs["idle_timeout"] = _handle_default(_val_to_sec(value))
                case "idlecheckfrequency":
                    redis_kwargs["idle_check_frequency"] = _handle_default(
                        _val_to_sec(value), condition=lambda x: x >= 1, default=1
                    )
                case "maxidleconns":
                    pool_kwargs["max_idle_connections"] = _handle_default(
                        int(value[0]), handle_zero=False
                    )
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

    return _set_config_defaults(pool_kwargs, redis_kwargs, tls_kwargs, url)


def _config_sentinel(config, service_name, credentials, kwargs, addrs):
    """Configure options for Redis sentinel"""
    if not service_name:
        raise ValueError("When using sentinel a mastername has to be specified!")
    sentinel_username, sentinel_password = credentials
    redis_kwargs, pool_kwargs = kwargs
    # Update username / password for sentinel connection
    sentinel_kwargs = deepcopy(redis_kwargs)
    # Set db to 0 for sentinel
    sentinel_kwargs["db"] = 0
    if sentinel_username:
        sentinel_kwargs["username"] = sentinel_username
    elif "username" in sentinel_kwargs:
        sentinel_kwargs.pop("username")
    if sentinel_password:
        sentinel_kwargs["password"] = sentinel_password
    elif "password" in sentinel_kwargs:
        sentinel_kwargs.pop("password")
    # Remove any unneeded host / port configuration
    redis_kwargs.pop("host", None)
    redis_kwargs.pop("port", None)
    config["type"] = "sentinel"
    config["pool_kwargs"] = deepcopy(pool_kwargs)
    config["redis_kwargs"] = deepcopy(redis_kwargs)
    config["service_name"] = service_name
    config["sentinels"] = []
    # Shuffle addrs similar to Go implementation
    shuffle(addrs)
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
    service_name = redis_kwargs.pop("service_name", None)
    sentinel_username = redis_kwargs.pop("sentinel_username", None)
    sentinel_password = redis_kwargs.pop("sentinel_password", None)
    scheme_parts = url.scheme.split("+")

    if scheme_parts[0] == "rediss":
        config["tls"] = True
        redis_kwargs |= tls_kwargs

    if len(scheme_parts) > 1:
        match scheme_parts[1]:
            case "sentinel" | "sentinels":
                redis_kwargs = _configure_tcp_keepalive(redis_kwargs)
                credentials = (sentinel_username, sentinel_password)
                kwargs = (redis_kwargs, pool_kwargs)
                config = _config_sentinel(config, service_name, credentials, kwargs, addrs)
            case "cluster" | "clusters":
                redis_kwargs = _configure_tcp_keepalive(redis_kwargs)
                config["type"] = "cluster"
                # Redis cluster only supports one DB, ignore...
                redis_kwargs.pop("db", None)
                config["pool_kwargs"] = deepcopy(pool_kwargs)
                config["redis_kwargs"] = deepcopy(redis_kwargs)
                config["addrs"] = addrs
                config["cluster_error_retry_attempts"] = cluster_error_retry_attempts
            case "socket":
                if scheme_parts[0] == "rediss":
                    raise ValueError("Redis unix socket connection does not support SSL!")
                redis_kwargs["path"] = url.path
                config["type"] = "socket"
                config["pool_kwargs"] = deepcopy(pool_kwargs)
                config["redis_kwargs"] = deepcopy(redis_kwargs)
            case _:
                raise ValueError("Unknown scheme found in redis connection URL: " + url.scheme)
    else:
        redis_kwargs = _configure_tcp_keepalive(redis_kwargs)

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
        connection_class_path = ""
        if config.get("tls", False):
            connection_class_path += "SSL"
        connection_class_path += "Connection"
        if config["type"] == "sentinel":
            config["redis_kwargs"]["connection_class"] = _get_class(
                "sentinel.SentinelManaged" + connection_class_path, use_async
            )
        if config["type"] == "socket":
            connection_class_path = "UnixDomainSocketConnection"
        connection_class_path = _get_class("connection." + connection_class_path, use_async)
        if callable(update_connection_class):
            connection_class_path = update_connection_class(connection_class_path)
        if config["type"] == "sentinel":
            config["redis_kwargs"]["internal_connection_class"] = connection_class_path
        else:
            config["redis_kwargs"]["connection_class"] = connection_class_path
    return config


def _retries_and_backoff(config, retry_class):
    """Configure retry and backoff similar to how go-redis handles it"""
    retries_and_backoff = config["redis_kwargs"].pop("retry")
    min_backoff = retries_and_backoff.get("min_backoff")
    max_backoff = retries_and_backoff.get("max_backoff")
    retries = retries_and_backoff.get("retry")
    config["redis_kwargs"]["retry"] = retry_class(
        FullJitterBackoff(
            cap=max_backoff if max_backoff is not None else DEFAULT_CAP,
            base=min_backoff if min_backoff is not None else DEFAULT_BASE,
        ),
        retries if retries is not None else DEFAULT_RETRIES,
    )
    config["redis_kwargs"].setdefault(
        "retry_on_error", [RedisConnectionError, RedisTimeoutError, SocketTimeout]
    )
    return config


def _get_class(class_path, use_async=False) -> Any:
    # Fix https://github.com/redis/redis-py/issues/626
    if class_path == "sentinel.Sentinel":
        module_path = "authentik.root.redis_middleware.Custom"
        if use_async:
            module_path += "Async"
        module_path += "Sentinel"
        return import_string(module_path)

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
            internal_connection_class = config["redis_kwargs"].pop("internal_connection_class")
            sentinel = _get_class("sentinel.Sentinel", use_async)(
                sentinels=[], **config["redis_kwargs"]
            )
            for sentinel_config in config["sentinels"]:
                sentinel_config["retry"] = config["redis_kwargs"]["retry"]
                sentinel_config["connection_class"] = internal_connection_class
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
