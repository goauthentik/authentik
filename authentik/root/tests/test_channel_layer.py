"""Tests for channel-layer database credential rotation."""

import asyncio
from contextlib import suppress
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from django_channels_postgres.layer import PostgresChannelLayer, PostgresChannelLoopLayer
from psycopg import OperationalError
from psycopg.conninfo import conninfo_to_dict


class TestChannelLayerCredentials(IsolatedAsyncioTestCase):
    """Pool retries must reload credentials after an authentication failure."""

    async def test_pool_retry_refreshes_credentials(self):
        params = {
            "dbname": "authentik",
            "password": "expired-token",
            "cursor_factory": None,
            "context": None,
        }
        database = Mock()
        database.get_connection_params.side_effect = params.copy
        passwords = []
        first_attempt = asyncio.Event()
        second_attempt = asyncio.Event()

        async def connect(conninfo, **kwargs):
            passwords.append(conninfo_to_dict(conninfo)["password"])
            if len(passwords) == 1:
                first_attempt.set()
            else:
                second_attempt.set()
            raise OperationalError("authentication failed")

        layer = PostgresChannelLoopLayer(PostgresChannelLayer())
        with (
            patch("django_channels_postgres.layer.connections", {"default": database}),
            patch("django_channels_postgres.layer.AsyncConnection.connect", side_effect=connect),
        ):
            opening = asyncio.create_task(layer.connection())
            try:
                await asyncio.wait_for(first_attempt.wait(), timeout=5)
                params["password"] = "fresh-token"
                await asyncio.wait_for(second_attempt.wait(), timeout=5)
                self.assertEqual(passwords[:2], ["expired-token", "fresh-token"])
            finally:
                opening.cancel()
                with suppress(asyncio.CancelledError):
                    await opening
                if layer._pool is not None:
                    await layer._pool.close()
