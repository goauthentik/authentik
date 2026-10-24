"""Tests for the Gunicorn to Uvicorn connection lifetime."""

import asyncio
import os
import socket
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from gunicorn.app.wsgiapp import WSGIApplication
from gunicorn.glogging import Logger
from prometheus_client import values
from uvicorn import Server


async def health_app(scope, receive, send):
    """A database-free ASGI endpoint for the real worker's HTTP protocol."""
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-length", b"2")],
        }
    )
    await send({"type": "http.response.body", "body": b"OK"})


class TestGunicornKeepAlive(IsolatedAsyncioTestCase):
    """An idle backend connection must remain reusable past the old two-second cutoff."""

    async def test_reuse_connection_after_two_seconds(self):
        config_path = Path(__file__).resolve().parents[3] / "lifecycle" / "gunicorn.conf.py"
        with (
            TemporaryDirectory() as directory,
            patch.dict(os.environ, {"CI": "true", "GUNICORN_CMD_ARGS": ""}),
            patch("sys.argv", ["gunicorn", "-c", str(config_path), "unused:app"]),
            patch("tempfile.gettempdir", return_value=directory),
            patch.object(values, "ValueClass", values.ValueClass),
            patch("authentik.root.setup.setup"),
            patch("authentik.lib.debug.start_debug_server"),
            patch("lifecycle.migrate.run_migrations"),
        ):
            # Load the shipped config and construct its actual worker. Only startup
            # side effects are disabled; Gunicorn/Uvicorn and their timers are real.
            application = WSGIApplication()
            worker = application.cfg.worker_class(
                0,
                os.getpid(),
                [],
                application,
                application.cfg.timeout,
                application.cfg,
                Logger(application.cfg),
            )
            worker.config.app = health_app
            worker.config.access_log = False
            server = Server(worker.config)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                socket_path = str(Path(directory) / "backend.sock")
                listener.bind(socket_path)
                listener.listen()
                listener.setblocking(False)
                serving = asyncio.create_task(server.serve(sockets=[listener]))
                writer = None
                try:
                    async with asyncio.timeout(5):
                        while not server.started:
                            if serving.done():
                                await serving
                            await asyncio.sleep(0.01)
                    reader, writer = await asyncio.open_unix_connection(socket_path)

                    async def request():
                        writer.write(b"GET /-/health/live/ HTTP/1.1\r\nHost: localhost\r\n\r\n")
                        await writer.drain()
                        headers = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 5)
                        self.assertTrue(headers.startswith(b"HTTP/1.1 200 "))
                        self.assertEqual(await asyncio.wait_for(reader.readexactly(2), 5), b"OK")

                    await request()
                    await asyncio.sleep(3)
                    self.assertFalse(
                        reader.at_eof(), "backend closed an otherwise healthy connection"
                    )
                    await request()
                finally:
                    if writer is not None:
                        writer.close()
                        await writer.wait_closed()
                    server.should_exit = True
                    await asyncio.wait_for(serving, 5)
