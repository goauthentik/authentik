"""PROTOTYPE (01b): regressions for the local interoperability probe."""

import asyncio
import importlib.util
import json
import os
import shutil
import signal
import socket
import time
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import skipUnless
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from django.conf import settings
from django.test import SimpleTestCase
from jwt import encode

SCRIPTS = Path(settings.BASE_DIR) / "scripts" / "cimd-prototype"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrototypeHarnessTestCase(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name)
        self.summary = load_script("summarize")

    def summary_text(self):
        output = StringIO()
        with redirect_stdout(output):
            self.summary.main(self.state)
        return output.getvalue()


class TestPrototypeHarness(PrototypeHarnessTestCase):
    def test_warm_cache_summary_and_client_id_classification(self):
        rows = [
            {
                "kind": "http",
                "ts": "2026-11-05T12:00:00+00:00",
                "method": "GET",
                "path": "/application/o/test/authorize/",
                "query": {"client_id": "https://client.invalid/metadata.json"},
                "form": {},
                "headers": {},
                "status": 302,
            },
            {
                "kind": "http",
                "ts": "2026-11-05T12:00:01+00:00",
                "method": "POST",
                "path": "/application/o/test/token/",
                "query": {},
                "form": {"client_id": "registered-client", "grant_type": "authorization_code"},
                "headers": {},
                "status": 200,
            },
        ]
        (self.state / "requests.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
        text = self.summary_text()
        self.assertIn("`https://client.invalid/metadata.json`: URL (CIMD), 1 requests", text)
        self.assertIn("`registered-client`: registered, 1 requests", text)
        self.assertIn("warm cache", text)
        self.assertNotIn("did not use a URL client_id", text)
        self.assertNotIn("(None, None)", text)

    def test_no_fetch_summary_is_inconclusive(self):
        (self.state / "mcp.jsonl").write_text(
            json.dumps({"kind": "token_rejected", "ts": "2026-11-05T12:00:00+00:00"})
        )
        self.assertIn("does not establish whether CIMD was used", self.summary_text())

    @skipUnless(shutil.which("jq"), "The probe's live log view requires jq")
    async def test_live_tail_follows_new_run_filename(self):
        (self.state / "akadmin-password").write_text("unused-test-fixture")
        log_path = self.state / "requests.jsonl"
        log_path.touch()
        env = {**os.environ, "CIMD_PROTOTYPE_STATE": str(self.state)}
        process = await asyncio.create_subprocess_exec(
            "/bin/bash",
            str(SCRIPTS / "run.sh"),
            "tail",
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        try:
            for name in ("before-rotation", "after-rotation"):
                deadline = time.monotonic() + 12
                observed = False
                while time.monotonic() < deadline:
                    with log_path.open("a") as log:
                        log.write(json.dumps({"ts": "2026-11-05T12:00:00", "kind": name}) + "\n")
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=0.25)
                    except TimeoutError:
                        continue
                    if name.encode() in line:
                        observed = True
                        break
                self.assertTrue(observed, f"live tail did not show {name}")
                if name == "before-rotation":
                    rotate = await asyncio.create_subprocess_exec(
                        "/bin/bash",
                        str(SCRIPTS / "run.sh"),
                        "new-run",
                        "regression",
                        env=env,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await asyncio.wait_for(rotate.communicate(), timeout=5)
                    self.assertEqual(rotate.returncode, 0)
            self.assertIsNone(process.returncode)
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            await asyncio.wait_for(process.communicate(), timeout=5)

    async def test_authentik_listener_environment(self):
        (self.state / "akadmin-password").write_text("unused-test-fixture")
        binaries = self.state / "bin"
        binaries.mkdir()
        for command, script in {
            "docker": "#!/bin/sh\nprintf '1\\n'\n",
            "uv": "#!/bin/sh\nenv | sort | grep '^AUTHENTIK_LISTEN__'\n",
        }.items():
            binary = binaries / command
            binary.write_text(script)
            binary.chmod(0o700)
        process = await asyncio.create_subprocess_exec(
            "/bin/bash",
            str(SCRIPTS / "run.sh"),
            "authentik",
            env={
                **os.environ,
                "CIMD_PROTOTYPE_STATE": str(self.state),
                "PATH": f"{binaries}:{os.environ['PATH']}",
            },
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
        self.assertEqual(process.returncode, 0, stderr.decode())
        values = dict(line.split("=", 1) for line in stdout.decode().splitlines())
        for listener, port in (("HTTP", 9000), ("HTTPS", 9443), ("METRICS", 9300)):
            self.assertEqual(
                values[f"AUTHENTIK_LISTEN__{listener}"], f"127.0.0.1:{port},[::1]:{port}"
            )
        self.assertEqual(values["AUTHENTIK_LISTEN__DEBUG"], "127.0.0.1:9900")
        self.assertEqual(values["AUTHENTIK_LISTEN__DEBUG_PY"], "127.0.0.1:9901")
        self.assertEqual(values["AUTHENTIK_LISTEN__DEBUG_TOKIO"], "[::1]:6669")


@skipUnless(importlib.util.find_spec("mcp"), "Install the probe's optional inline MCP dependencies")
class TestPrototypeMCP(PrototypeHarnessTestCase):
    def setUp(self):
        super().setUp()
        with patch.dict(os.environ, {"CIMD_PROTOTYPE_STATE": str(self.state)}):
            self.server = load_script("mcp_server")

    def test_state_override(self):
        self.server.record("state_probe")
        self.assertEqual(self.server.LOG, self.state / "mcp.jsonl")
        self.assertEqual(self.summary.load(self.server.LOG)[0]["kind"], "state_probe")

    def test_mcp_loopback_sockets(self):
        def inspect_sockets(*, sockets):
            self.assertEqual(
                {listener.getsockname()[0] for listener in sockets}, {"127.0.0.1", "::1"}
            )
            for listener in sockets:
                listener.listen()
                with socket.socket(listener.family, socket.SOCK_STREAM) as connection:
                    connection.settimeout(2)
                    connection.connect(listener.getsockname())
                with listener.accept()[0]:
                    pass

        with patch.object(self.server.uvicorn.Server, "run", side_effect=inspect_sockets) as run:
            self.server.serve(self.server.create_app("http://localhost:9000/", "provider"), 0)
        run.assert_called_once()

    def test_wrong_audience_rejected_by_http_and_summary(self):
        from starlette.testclient import TestClient

        issuer = "http://localhost:9000/application/o/test/"
        key = generate_private_key(public_exponent=65537, key_size=2048)
        token = encode(
            {
                "iss": issuer,
                "sub": "test-user",
                "aud": "wrong-audience",
                "exp": int(time.time()) + 60,
            },
            key,
            algorithm="RS256",
        )
        with patch.object(
            self.server.jwt.PyJWKClient,
            "get_signing_key_from_jwt",
            return_value=SimpleNamespace(key=key.public_key()),
        ):
            with TestClient(
                self.server.create_app(issuer, "provider"), base_url="http://localhost:8765"
            ) as client:
                response = client.post("/mcp", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 401)
        rows = self.summary.load(self.server.LOG)
        self.assertFalse(any(row["kind"] == "token_accepted" for row in rows))
        self.assertTrue(any(row.get("error") == "invalid_audience" for row in rows))
        self.assertIn("Tokens accepted: 0, rejected: 1", self.summary_text())

    def test_valid_audiences_log_only_acceptance(self):
        issuer = "http://localhost:9000/application/o/test/"
        resource = "http://localhost:8765/mcp"
        key = generate_private_key(public_exponent=65537, key_size=2048)
        verifier = self.server.JWTVerifier(issuer, "provider", resource)
        with patch.object(
            verifier.jwks,
            "get_signing_key_from_jwt",
            return_value=SimpleNamespace(key=key.public_key()),
        ):
            for audience in ("provider", resource, [resource, "provider"]):
                token = encode(
                    {
                        "iss": issuer,
                        "sub": "test-user",
                        "aud": audience,
                        "exp": int(time.time()) + 60,
                    },
                    key,
                    algorithm="RS256",
                )
                self.assertIsNotNone(asyncio.run(verifier.verify_token(token)))
        rows = self.summary.load(self.server.LOG)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["kind"] == "token_accepted" for row in rows))
        self.assertTrue(rows[0]["aud_is_provider"])
        self.assertFalse(rows[0]["aud_is_resource"])
        self.assertTrue(rows[1]["aud_is_resource"])
        self.assertIn("Tokens accepted: 3, rejected: 0", self.summary_text())
