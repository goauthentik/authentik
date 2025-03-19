"""Test Redis URL parser"""

from asyncio import PriorityQueue
from importlib import reload
from unittest.mock import patch
from urllib.parse import urlparse

from _socket import TCP_KEEPCNT, TCP_KEEPINTVL
from django.test import TestCase
from redis import BlockingConnectionPool, RedisCluster, SentinelConnectionPool
from redis.backoff import DEFAULT_BASE, DEFAULT_CAP, FullJitterBackoff
from redis.retry import Retry

import authentik.lib.utils.parser
from authentik.lib.utils.parser import (
    DEFAULT_RETRIES,
    get_connection_pool,
    get_redis_options,
    process_config,
)


# pylint: disable=too-many-public-methods
class TestParserUtils(TestCase):
    """Test Redis URL parser"""

    def test_process_config(self):
        """Test Redis URL parser for direct Redis connection"""
        url = urlparse("redis://myredis:5678/34")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "default")
        self.assertEqual(config["redis_kwargs"]["host"], "myredis")
        self.assertEqual(config["redis_kwargs"]["port"], 5678)
        self.assertEqual(config["redis_kwargs"]["db"], 34)

    def test_process_config_sentinel(self):
        """Test Redis URL parser for Sentinel connection"""
        url = urlparse(
            "redis+sentinel://username:password@mysentinel:22345/92?mastername=themaster"
        )
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "sentinel")
        self.assertEqual(config["sentinels"][0]["host"], "mysentinel")
        self.assertEqual(config["sentinels"][0]["port"], 22345)
        self.assertEqual(config["sentinels"][0]["db"], 0)

    def test_process_config_cluster(self):
        """Test Redis URL parser for cluster connection"""
        url = urlparse("redis+cluster://mycluster:8652/393")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "cluster")
        self.assertEqual(config["addrs"][0][0], "mycluster")
        self.assertEqual(config["addrs"][0][1], 8652)
        self.assertTrue("db" not in config["redis_kwargs"])

    def test_get_redis_options_addr_arg(self):
        """Test Redis URL parser with addr arg"""
        url = urlparse("redis://myredis:6379/0?addr=newmyredis")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("newmyredis", 6379), ("myredis", 6379)])

    def test_get_redis_options_addr_arg_no_host(self):
        """Test Redis URL parser with addr arg but no host"""
        url = urlparse("redis:///0?addr=newmyredis")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("newmyredis", 6379)])

    def test_get_redis_options_no_addr_arg_no_host(self):
        """Test Redis URL parser without addr arg and no host"""
        url = urlparse("redis:///0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("127.0.0.1", 6379)])

    def test_get_redis_options_no_addr_arg_no_host_sentinel(self):
        """Test Redis URL parser without addr arg and no host"""
        url = urlparse("redis+sentinel:///0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("127.0.0.1", 26379)])

    def test_get_redis_options_addrs_arg(self):
        """Test Redis URL parser with addrs arg"""
        url = urlparse("redis://myredis:6379/0?addrs=newmyredis:1234,otherredis")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(
            redis_kwargs["addrs"], [("newmyredis", 1234), ("otherredis", 6379), ("myredis", 6379)]
        )

    def test_get_redis_options_redis_credentials(self):
        """Test Redis URL parser with basic auth credentials"""
        url = urlparse("redis://redis:password@myredis/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["username"], "redis")
        self.assertEqual(redis_kwargs["password"], "password")

    def test_get_redis_options_redis_username_arg(self):
        """Test Redis URL parser with username arg"""
        url = urlparse("redis://redis:password@myredis/0?username=newredis")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["username"], "newredis")

    def test_get_redis_options_only_redis_username(self):
        """Test Redis URL parser with only username in basic auth"""
        url = urlparse("redis://redis:@myredis/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["username"], "redis")

    def test_get_redis_options_redis_password_arg(self):
        """Test Redis URL parser with password arg"""
        url = urlparse("redis://redis:password@myredis/0?password=%22%27%25+%21.%3B.%C2%B0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["password"], "\"'% !.;.°")

    def test_get_redis_options_only_redis_password(self):
        """Test Redis URL parser with only password in basic auth"""
        url = urlparse("redis://password@myredis/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["password"], "password")

    def test_get_redis_options_database_arg(self):
        """Test Redis URL parser with password arg"""
        url = urlparse("redis://password@myredis?database=15")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["db"], 15)

    def test_get_redis_options_db_arg(self):
        """Test Redis URL parser with password arg"""
        url = urlparse("redis://password@myredis?db=10")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["db"], 10)

    def test_get_redis_options_max_retries_arg(self):
        """Test Redis URL parser with maxretries arg"""
        url = urlparse("redis://myredis:6379/0?maxretries=123")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["cluster_error_retry_attempts"], 123)

    def test_get_redis_options_max_retries_arg_negative_number(self):
        """Test Redis URL parser with negative maxretries arg"""
        url = urlparse("redis://myredis:6379/0?maxretries=-432")
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        self.assertEqual(redis_kwargs["retry"]["retry"], 0)
        config = process_config(url, pool_kwargs, redis_kwargs, tls_kwargs)
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertEqual(retry_config._retries, 0)

    def test_get_redis_options_min_retry_backoff_arg(self):
        """Test Redis URL parser with minretrybackoff arg"""
        url = urlparse("redis://myredis/0?minretrybackoff=100s")
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        self.assertEqual(redis_kwargs["retry"]["min_backoff"], 100)
        config = process_config(url, pool_kwargs, redis_kwargs, tls_kwargs)
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, 100)
        self.assertEqual(retry_config._backoff._cap, DEFAULT_CAP)

    def test_get_redis_options_min_retry_backoff_arg_negative_number(self):
        """Test Redis URL parser with negative minretrybackoff arg"""
        url = urlparse("redis://myredis/0?minretrybackoff=-52s")
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        self.assertEqual(redis_kwargs["retry"]["min_backoff"], 0)
        config = process_config(url, pool_kwargs, redis_kwargs, tls_kwargs)
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, 0)
        self.assertEqual(retry_config._backoff._cap, DEFAULT_CAP)

    def test_get_redis_options_max_retry_backoff_arg(self):
        """Test Redis URL parser with maxretrybackoff arg"""
        url = urlparse("redis://myredis/0?maxretrybackoff=100s")
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        self.assertEqual(redis_kwargs["retry"]["max_backoff"], 100)
        config = process_config(url, pool_kwargs, redis_kwargs, tls_kwargs)
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, DEFAULT_BASE)
        self.assertEqual(retry_config._backoff._cap, 100)

    def test_get_redis_options_max_retry_backoff_arg_negative_number(self):
        """Test Redis URL parser with negative maxretrybackoff arg"""
        url = urlparse("redis://myredis/0?maxretrybackoff=-13s")
        pool_kwargs, redis_kwargs, tls_kwargs = get_redis_options(url)
        self.assertEqual(redis_kwargs["retry"]["max_backoff"], 0)
        config = process_config(url, pool_kwargs, redis_kwargs, tls_kwargs)
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, DEFAULT_BASE)
        self.assertEqual(retry_config._backoff._cap, 0)

    def test_get_connection_pool_max_retries(self):
        """Test ConnectionPool generator with maxretries"""
        url = urlparse("redis://myredis:6379/0?maxretries=123")
        config = process_config(url, *get_redis_options(url))
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertEqual(retry_config._retries, 123)

    def test_get_connection_pool_max_retries_and_min_and_max_backoff_default(self):
        """Test ConnectionPool generator retrie and backoff defaults"""
        url = urlparse("redis://myredis:6379/0")
        config = process_config(url, *get_redis_options(url))
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, DEFAULT_BASE)
        self.assertEqual(retry_config._backoff._cap, DEFAULT_CAP)
        self.assertEqual(retry_config._retries, DEFAULT_RETRIES)

    def test_get_connection_pool_max_retries_and_min_and_max_backoff(self):
        """Test ConnectionPool generator with maxretries, minretrybackoff and maxretrybackoff"""
        url = urlparse("redis://myredis:6379/0?maxretries=32&minretrybackoff=4s&maxretrybackoff=8s")
        config = process_config(url, *get_redis_options(url))
        connection_pool, _ = get_connection_pool(config)
        retry_config = connection_pool.connection_kwargs["retry"]
        self.assertIsInstance(retry_config, Retry)
        self.assertIsInstance(retry_config._backoff, FullJitterBackoff)
        self.assertEqual(retry_config._backoff._base, 4)
        self.assertEqual(retry_config._backoff._cap, 8)
        self.assertEqual(retry_config._retries, 32)

    def test_get_connection_pool_sentinel(self):
        """Test ConnectionPool generator for sentinel"""
        url = urlparse("redis+sentinel://myredis:26379/0?mastername=mymaster")
        config = process_config(url, *get_redis_options(url))
        connection_pool, _ = get_connection_pool(config)
        self.assertIsInstance(connection_pool, SentinelConnectionPool)

    def test_get_connection_pool_cluster(self):
        """Test ConnectionPool generator for cluster"""
        url = urlparse("redis+cluster://myredis:6379")
        config = process_config(url, *get_redis_options(url))
        _, client_config = get_connection_pool(config)
        self.assertEqual(client_config["client_class"], RedisCluster)

    def test_get_connection_pool_socket(self):
        """Test ConnectionPool generator for socket"""
        url = urlparse("redis+socket://mysocket.sock/0")
        config = process_config(url, *get_redis_options(url))
        connection_pool, _ = get_connection_pool(config)
        self.assertIsInstance(connection_pool, BlockingConnectionPool)

    def test_get_redis_options_timeout_arg(self):
        """Test Redis URL parser with timeout arg"""
        url = urlparse("redis://myredis/0?timeout=100s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 100)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 100)

    def test_get_redis_options_timeout_arg_empty(self):
        """Test Redis URL parser with empty timeout arg"""
        url = urlparse("redis://myredis/0?timeout=")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 3)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 5)

    def test_get_redis_options_timeout_arg_invalid_format(self):
        """Test Redis URL parser with invalid format timeout arg"""
        url = urlparse("redis://myredis/0?timeout=39l")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 3)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 5)

    def test_get_redis_options_timeout_arg_invalid_char(self):
        """Test Redis URL parser with invalid char timeout arg"""
        url = urlparse("redis://myredis/0?timeout=39,34h")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 3)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 5)

    def test_get_redis_options_timeout_arg_missing_unit(self):
        """Test Redis URL parser with missing unit timeout arg"""
        url = urlparse("redis://myredis/0?timeout=43")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 43)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 43)

    def test_get_redis_options_timeout_arg_no_number(self):
        """Test Redis URL parser with no number timeout arg"""
        url = urlparse("redis://myredis/0?timeout=ms")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 3)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 5)

    def test_get_redis_options_timeout_arg_negative_number(self):
        """Test Redis URL parser with negative timeout arg"""
        url = urlparse("redis://myredis/0?timeout=-8s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 0)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 0)

    def test_get_redis_options_timeout_arg_milliseconds(self):
        """Test Redis URL parser with millisecond timeout arg"""
        url = urlparse("redis://myredis/0?timeout=10000ms")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 10)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 10)

    def test_get_redis_options_dial_timeout_arg(self):
        """Test Redis URL parser with dialtimeout arg"""
        url = urlparse("redis://myredis/0?dialtimeout=100s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 100)

    def test_get_redis_options_dial_timeout_arg_negative_number(self):
        """Test Redis URL parser with negative dialtimeout arg"""
        url = urlparse("redis://myredis/0?dialtimeout=-32s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_connect_timeout"], 0)

    def test_get_redis_options_read_timeout_arg(self):
        """Test Redis URL parser with readtimeout arg"""
        url = urlparse("redis://myredis/0?readtimeout=100s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 100)

    def test_get_redis_options_read_timeout_arg_negative_number(self):
        """Test Redis URL parser with negative readtimeout arg"""
        url = urlparse("redis://myredis/0?readtimeout=-36s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], None)

    def test_get_redis_options_write_timeout_arg(self):
        """Test Redis URL parser with writetimeout arg"""
        url = urlparse("redis://myredis/0?writetimeout=100s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], 100)

    def test_get_redis_options_write_timeout_arg_negative_number(self):
        """Test Redis URL parser with negative writetimeout arg"""
        url = urlparse("redis://myredis/0?writetimeout=-91s")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["socket_timeout"], None)

    def test_get_redis_options_pool_fifo_arg(self):
        """Test Redis URL parser with poolfifo arg"""
        url = urlparse("redis://myredis/0?poolfifo=true")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertEqual(pool_kwargs["queue_class"], PriorityQueue)

    def test_get_redis_options_pool_fifo_arg_fallback(self):
        """Test Redis URL parser with bad poolfifo arg

        No queue class shall be set in this case and
        instead the default asyncio.LifoQueue of the
        BlockingConnectionPool is used
        """
        url = urlparse("redis://myredis/0?poolfifo=abc")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertTrue("queue_class" not in pool_kwargs)

    def test_get_redis_options_pool_size_arg(self):
        """Test Redis URL parser with poolsize arg"""
        url = urlparse("redis://myredis/0?poolsize=32")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertEqual(pool_kwargs["max_connections"], 32)

    def test_get_redis_options_pool_size_arg_fallback(self):
        """Test Redis URL parser for fallback poolsize value"""
        with patch("os.sched_getaffinity", side_effect=ImportError):
            reload(authentik.lib.utils.parser)
            url = urlparse("redis://myredis/0")
            pool_kwargs, _, _ = get_redis_options(url)
            self.assertEqual(pool_kwargs["max_connections"], 50)
        reload(authentik.lib.utils.parser)

    def test_get_redis_options_pool_timeout_arg(self):
        """Test Redis URL parser with pooltimeout arg"""
        url = urlparse("redis://myredis/0?pooltimeout=100s")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertEqual(pool_kwargs["timeout"], 100)

    def test_get_redis_options_pool_timeout_arg_negative_number(self):
        """Test Redis URL parser with negative pooltimeout arg"""
        url = urlparse("redis://myredis/0?pooltimeout=-100s")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertEqual(pool_kwargs["timeout"], 0)

    def test_get_redis_options_idle_timeout_arg(self):
        """Test Redis URL parser with idletimeout arg"""
        url = urlparse("redis://myredis/0?idletimeout=100s")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["redis_kwargs"]["socket_keepalive_options"][TCP_KEEPCNT], 100 // 60)

    def test_get_redis_options_idle_timeout_arg_socket(self):
        """Test Redis URL parser with idletimeout arg for Redis socket connection"""
        url = urlparse("redis+socket://myredis/0?idletimeout=100s")
        config = process_config(url, *get_redis_options(url))
        self.assertFalse("socket_keepalive_options" in config["redis_kwargs"])

    # TODO: This is not supported by the Go Redis URL parser!
    def test_get_redis_options_idle_check_frequency_arg(self):
        """Test Redis URL parser with idlecheckfrequency arg"""
        url = urlparse("redis://myredis/0?idlecheckfrequency=31s")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["redis_kwargs"]["socket_keepalive_options"][TCP_KEEPINTVL], 31)

    def test_get_redis_options_keepalive_linux(self):
        """Test keepalive setting for Linux"""
        with patch("sys.platform", "linux"):
            with patch("socket.TCP_KEEPIDLE", 29, create=True):
                reload(authentik.lib.utils.parser)
                url = urlparse("redis://myredis/0")
                config = process_config(url, *get_redis_options(url))
                self.assertEqual(config["redis_kwargs"]["socket_keepalive_options"][29], 5 * 60)
        reload(authentik.lib.utils.parser)

    def test_get_redis_options_keepalive_darwin(self):
        """Test keepalive setting for macOS"""
        with patch("sys.platform", "darwin"):
            with patch("socket.TCP_KEEPALIVE", 32, create=True):
                reload(authentik.lib.utils.parser)
                url = urlparse("redis://myredis/0")
                config = process_config(url, *get_redis_options(url))
                self.assertEqual(config["redis_kwargs"]["socket_keepalive_options"][32], 5 * 60)
        reload(authentik.lib.utils.parser)

    # TODO: This is not supported by the Go Redis URL parser!
    def test_get_redis_options_idle_check_frequency_arg_socket(self):
        """Test Redis URL parser with idlecheckfrequency arg for Redis socket connection"""
        url = urlparse("redis+socket://myredis/0?idlecheckfrequency=42s")
        config = process_config(url, *get_redis_options(url))
        self.assertFalse("socket_keepalive_options" in config["redis_kwargs"])

    def test_get_redis_options_max_idle_conns_arg(self):
        """Test Redis URL parser with maxidleconns arg"""
        url = urlparse("redis://myredis/0?maxidleconns=52")
        pool_kwargs, _, _ = get_redis_options(url)
        self.assertEqual(pool_kwargs["max_idle_connections"], 52)

    def test_get_redis_options_sentinel_master_id_arg(self):
        """Test Redis URL parser with sentinelmasterid arg"""
        url = urlparse("redis://myredis/0?sentinelmasterid=themaster")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["service_name"], "themaster")

    def test_get_redis_options_master_name_arg(self):
        """Test Redis URL parser with mastername arg"""
        url = urlparse("redis://myredis/0?mastername=themaster")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["service_name"], "themaster")

    def test_get_redis_options_sentinel_credentials(self):
        """Test Redis URL parser with sentinelusername and sentinelpassword arg"""
        url = urlparse(
            "redis+sentinel://redis:password@myredis/0"
            + "?mastername=mymaster&sentinelusername=suser&sentinelpassword=spass"
        )
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["sentinels"][0]["username"], "suser")
        self.assertEqual(config["sentinels"][0]["password"], "spass")

    def test_get_redis_options_sentinel_no_mastername(self):
        """Test Redis URL parser with missing mastername for sentinel"""
        url = urlparse("redis+sentinel://myredis/0")
        with self.assertRaises(ValueError):
            process_config(url, *get_redis_options(url))

    def test_get_redis_options_readonly_arg(self):
        """Test Redis URL parser with readonly arg"""
        url = urlparse("redis://myredis/0?readonly=true")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["readonly"], True)

    def test_get_redis_options_skip_verify_arg(self):
        """Test Redis URL parser with skipverify arg"""
        url = urlparse("redis://myredis/0?skipverify=true")
        _, _, tls_kwargs = get_redis_options(url)
        self.assertEqual(tls_kwargs["ssl_cert_reqs"], "optional")

    def test_get_redis_options_insecure_skip_verify_arg(self):
        """Test Redis URL parser with insecureskipverify arg"""
        url = urlparse("redis://myredis/0?insecureskipverify=true")
        _, _, tls_kwargs = get_redis_options(url)
        self.assertEqual(tls_kwargs["ssl_cert_reqs"], "none")

    def test_get_redis_options_minidleconns_arg(self):
        """Test Redis URL parser with minidleconns arg"""
        url = urlparse("redis://myredis/0?minidleconns=4")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertFalse("minidleconns" in redis_kwargs)
        self.assertFalse("min_idle_conns" in redis_kwargs)

    def test_get_redis_options_unknown_arg(self):
        """Test Redis URL parser with an unknown arg"""
        url = urlparse("redis://myredis/0?notanarg=4")
        with self.assertRaises(ValueError):
            get_redis_options(url)

    def test_get_redis_options_invalid_port(self):
        """Test Redis URL parser with an unknown arg"""
        url = urlparse("redis://myredis:invalid/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("127.0.0.1", 6379)])

    def test_convert_string_to_bool_valid(self):
        """Test correct conversion of string to bool"""
        url = urlparse("redis://myredis/0?readonly=False")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertFalse(redis_kwargs["readonly"])

    def test_convert_string_to_bool_invalid(self):
        """Test failing conversion of string to bool"""
        url = urlparse("redis://myredis/0?readonly=TrUe")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertFalse(redis_kwargs["readonly"])

    def test_ipv6_host_address(self):
        """Test correct parsing of IPv6 addresses"""
        url = urlparse("redis://[2001:1:2:3:4::5]:2932/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("[2001:1:2:3:4::5]", 2932)])  #

    def test_ipv6_host_address_no_port(self):
        """Test correct parsing of IPv6 addresses without port"""
        url = urlparse("redis://[2001:1:2:3:4::5]/0")
        _, redis_kwargs, _ = get_redis_options(url)
        self.assertEqual(redis_kwargs["addrs"], [("[2001:1:2:3:4::5]", 6379)])

    def test_socket_tls_unsupported(self):
        """Test failure if trying to use TLS for socket connection"""
        url = urlparse("rediss+socket://test.sock")
        with self.assertRaises(ValueError):
            process_config(url, *get_redis_options(url))

    def test_unsupported_scheme(self):
        """Test failure if trying to use unknown scheme"""
        url = urlparse("invalid://myredis/0")
        with self.assertRaises(ValueError):
            process_config(url, *get_redis_options(url))

    def test_unsupported_scheme_part(self):
        """Test failure if trying to use unknown scheme part"""
        url = urlparse("redis+invalid://myredis/0")
        with self.assertRaises(ValueError):
            process_config(url, *get_redis_options(url))
