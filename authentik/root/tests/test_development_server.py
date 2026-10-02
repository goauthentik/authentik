"""Native development server lifecycle tests."""

import signal
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch

from uvicorn import Config

from lifecycle.server import WORKER_ID, DevelopmentServer, main


class TestDevelopmentServer(IsolatedAsyncioTestCase):
    """Readiness must follow socket startup, and shutdown must clean live metrics."""

    async def test_readiness_after_startup(self):
        server = DevelopmentServer(Config(Mock(), log_config=None))

        async def started(**kwargs):
            server.started = True

        with (
            patch("uvicorn.Server.startup", side_effect=started) as startup,
            patch("lifecycle.server.os.getppid", return_value=123),
            patch("lifecycle.server.os.kill") as kill,
        ):
            await server.startup()
        startup.assert_awaited_once_with(sockets=None)
        kill.assert_called_once_with(123, signal.SIGUSR1)

    async def test_failed_startup_does_not_notify_supervisor(self):
        server = DevelopmentServer(Config(Mock(), log_config=None))
        with (
            patch("uvicorn.Server.startup", side_effect=OSError("bind failed")),
            patch("lifecycle.server.os.kill") as kill,
        ):
            with self.assertRaisesRegex(OSError, "bind failed"):
                await server.startup()
        kill.assert_not_called()

    async def test_shutdown_cleans_metrics_even_on_error(self):
        server = DevelopmentServer(Config(Mock(), log_config=None))
        for error in (None, RuntimeError("shutdown failed")):
            with (
                self.subTest(error=error),
                patch("uvicorn.Server.shutdown", new=AsyncMock(side_effect=error)) as shutdown,
                patch("lifecycle.server.multiprocess.mark_process_dead") as cleanup,
            ):
                if error:
                    with self.assertRaisesRegex(RuntimeError, "shutdown failed"):
                        await server.shutdown()
                else:
                    await server.shutdown()
                shutdown.assert_awaited_once_with(sockets=None)
                cleanup.assert_called_once_with(WORKER_ID)


class TestDevelopmentServerBootstrap(TestCase):
    """Preserve Django startup hooks in the non-forking runner."""

    def test_bootstrap_before_serving(self):
        calls = Mock()
        with (
            patch("lifecycle.server.values.ValueClass"),
            patch("lifecycle.server.MultiProcessValue", return_value=Mock()),
            patch("lifecycle.server.setup", new=calls.setup),
            patch("lifecycle.server.run_migrations", new=calls.migrate),
            patch("authentik.root.asgi.application") as application,
            patch("lifecycle.server.start_debug_server", new=calls.debug),
            patch("lifecycle.server.start_pyroscope", new=calls.profile),
            patch("lifecycle.server.DevelopmentServer") as server,
        ):
            calls.attach_mock(application.call_startup, "startup")
            calls.attach_mock(server.return_value.run, "serve")
            main("/tmp/authentik test.sock")

        self.assertEqual(
            [call[0] for call in calls.mock_calls],
            ["setup", "migrate", "debug", "profile", "startup", "serve"],
        )
        config = server.call_args.args[0]
        self.assertEqual(config.uds, "/tmp/authentik test.sock")
        self.assertEqual(config.workers, 1)
        self.assertEqual(config.lifespan, "off")
        self.assertEqual(config.timeout_graceful_shutdown, 30)
        self.assertIsNone(config.limit_max_requests)
