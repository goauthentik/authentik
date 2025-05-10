"""test SCIM Source"""

from pprint import pformat
from time import sleep

from docker.types import Healthcheck

from authentik.crypto.generators import generate_id
from authentik.lib.utils.http import get_http_session
from authentik.sources.scim.models import SCIMSource
from tests.e2e.utils import SeleniumTestCase, retry

TEST_POLL_MAX = 25


class TestSourceSCIM(SeleniumTestCase):
    """test SCIM Source flow"""

    def setUp(self):
        self.slug = generate_id()
        super().setUp()
        self.run_container(
            image=(
                "ghcr.io/suvera/scim2-compliance-test-utility@sha256:eca913bb73"
                "c46892cd1fb2dfd2fef1c5881e6abc5cb0eec7e92fb78c1b933ece"
            ),
            ports={"8080": "8080"},
            healthcheck=Healthcheck(
                test=["CMD", "curl", "http://localhost:8080"],
                interval=5 * 1_000 * 1_000_000,
                start_period=1 * 1_000 * 1_000_000,
            ),
        )

    @retry()
    def test_scim_conformance(self):
        source = SCIMSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
        )
        session = get_http_session()
        test_launch = session.post(
            "http://localhost:8080/test/run",
            data={
                "endPoint": self.live_server_url + f"/source/scim/{source.slug}/v2",
                "username": "foo",
                "password": source.token.key,
                "jwtToken": None,
                "usersCheck": 1,
                "groupsCheck": 1,
                "checkIndResLocation": 1,
            },
        )
        self.assertEqual(test_launch.status_code, 200)
        test_id = test_launch.json()["id"]
        attempt = 0
        while attempt <= TEST_POLL_MAX:
            test_status = session.get(
                "http://localhost:8080/test/status",
                params={"runId": test_id},
            )
            self.assertEqual(test_status.status_code, 200)
            body = test_status.json()
            if any([data["title"] == "--DONE--" for data in body["data"]]):
                break
            attempt += 1
            sleep(1)
        for test in body["data"]:
            # Workaround, the test expects DELETE requests to return 204 and have
            # the content type set to the JSON SCIM one, which is not what most HTTP servers do
            if test["requestMethod"] == "DELETE" and test["responseCode"] == 204:  # noqa: PLR2004
                continue
            if test["title"] == "--DONE--":
                break
            self.assertTrue(test["success"], pformat(test))
