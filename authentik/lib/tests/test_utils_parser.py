from urllib.parse import urlparse

from django.test import TestCase

from authentik.lib.utils.parser import get_redis_options, process_config


# TODO: Add tests for all possible parser options
class TestParserUtils(TestCase):
    def test_process_config(self):
        url = urlparse("redis://myredis:5678/34")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "default")
        self.assertEqual(config["redis_kwargs"]["host"], "myredis")
        self.assertEqual(config["redis_kwargs"]["port"], 5678)
        self.assertEqual(config["redis_kwargs"]["db"], 34)

    def test_process_config_sentinel(self):
        url = urlparse("redis+sentinel://mysentinel:22345/92?mastername=themaster")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "sentinel")
        self.assertEqual(config["sentinels"][0]["host"], "mysentinel")
        self.assertEqual(config["sentinels"][0]["port"], 22345)
        self.assertEqual(config["sentinels"][0]["db"], 92)

    def test_process_config_cluster(self):
        url = urlparse("redis+cluster://mycluster:8652/85")
        config = process_config(url, *get_redis_options(url))
        self.assertEqual(config["type"], "cluster")
        self.assertEqual(config["client_kwargs"]["startup_nodes"][0].host, "mycluster")
        self.assertEqual(config["client_kwargs"]["startup_nodes"][0].port, "8652")
