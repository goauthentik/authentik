"""Tests for the browser-facing RAC WebSocket consumer."""

from unittest.mock import AsyncMock, MagicMock

from django.test import SimpleTestCase

from authentik.providers.rac.consumer_client import RACClientConsumer
from authentik.providers.rac.guacamole import (
    GuacamoleInstructionParser,
    GuacamoleProtocolError,
)
from authentik.providers.rac.models import ConnectionToken

PING = "0.,4.ping,13.1700000000000;"
MOUSE = "5.mouse,1.1,1.2,1.0;"
KEY = "3.key,2.65,1.1;"


class TestGuacamoleInstructionParser(SimpleTestCase):
    """Test Guacamole framing and size handling."""

    def test_delimiters_inside_element_contents_are_preserved(self):
        instruction = "4.test,5.a,b;c;"

        parser = GuacamoleInstructionParser()
        responses, forwarded = parser.split_internal(parser.feed(instruction))

        self.assertEqual([], responses)
        self.assertEqual(instruction, forwarded)

    def test_non_bmp_instruction_size_uses_utf16_units(self):
        content = "😀" * 4092
        instruction = f"4.test,{len(content) * 2}.{content};"
        parser = GuacamoleInstructionParser()

        with self.assertRaises(GuacamoleProtocolError):
            parser.feed(instruction)

        responses, forwarded = parser.split_internal(parser.feed("3.nop;"))
        self.assertEqual([], responses)
        self.assertEqual("3.nop;", forwarded)


class TestRACClientConsumer(SimpleTestCase):
    """Test Guacamole tunnel instruction handling."""

    def setUp(self):
        self.consumer = RACClientConsumer()
        self.consumer.dest_channel_id = "outpost-channel"
        self.consumer.token = MagicMock(spec=ConnectionToken)
        self.consumer.token.is_expired = False
        self.logger = MagicMock()
        self.consumer.logger = self.logger
        self.consumer.guacamole_parser = GuacamoleInstructionParser()
        self.channel_send = AsyncMock()
        self.consumer.channel_layer = MagicMock()
        self.consumer.channel_layer.send = self.channel_send
        self.browser_send = AsyncMock()
        self.consumer.send = self.browser_send
        self.disconnect = AsyncMock()
        self.consumer.event_disconnect = self.disconnect

    async def test_internal_ping_is_echoed(self):
        await self.consumer.receive(text_data=PING)

        self.browser_send.assert_awaited_once_with(text_data=PING)
        self.channel_send.assert_not_awaited()
        self.disconnect.assert_not_awaited()

    async def test_normal_instruction_is_forwarded_unchanged(self):
        await self.consumer.receive(text_data="3.nop;")

        self.browser_send.assert_not_awaited()
        self.channel_send.assert_awaited_once_with(
            "outpost-channel",
            {
                "type": "event.send",
                "text_data": "3.nop;",
            },
        )

    async def test_utf16_element_length_is_forwarded_unchanged(self):
        instruction = "4.test,2.😀;"

        await self.consumer.receive(text_data=instruction)

        self.channel_send.assert_awaited_once_with(
            "outpost-channel",
            {
                "type": "event.send",
                "text_data": instruction,
            },
        )

    async def test_multiple_instructions_filter_ping(self):
        await self.consumer.receive(text_data=MOUSE + PING + KEY)

        self.browser_send.assert_awaited_once_with(text_data=PING)
        self.channel_send.assert_awaited_once_with(
            "outpost-channel",
            {
                "type": "event.send",
                "text_data": MOUSE + KEY,
            },
        )

    async def test_binary_frames_are_ignored(self):
        await self.consumer.receive(bytes_data=(MOUSE + PING + KEY).encode())

        self.browser_send.assert_not_awaited()
        self.channel_send.assert_not_awaited()

    async def test_unknown_internal_instruction_is_filtered(self):
        await self.consumer.receive(text_data="0.,7.unknown,5.value;")

        self.browser_send.assert_not_awaited()
        self.channel_send.assert_not_awaited()

    async def test_malformed_instruction_is_ignored_and_parser_recovers(self):
        await self.consumer.receive(text_data="x.mouse,1.1;")
        await self.consumer.receive(text_data=KEY)

        self.browser_send.assert_not_awaited()
        self.channel_send.assert_awaited_once_with(
            "outpost-channel",
            {
                "type": "event.send",
                "text_data": KEY,
            },
        )
        self.logger.debug.assert_called_once()

    async def test_fragmented_ping_is_echoed_once_complete(self):
        await self.consumer.receive(text_data=PING[:10])

        self.browser_send.assert_not_awaited()
        self.channel_send.assert_not_awaited()

        await self.consumer.receive(text_data=PING[10:])

        self.browser_send.assert_awaited_once_with(text_data=PING)
        self.channel_send.assert_not_awaited()

    async def test_repeated_pings_do_not_disconnect_or_relay(self):
        await self.consumer.receive(text_data=PING)
        await self.consumer.receive(text_data=PING)

        self.assertEqual(self.browser_send.await_count, 2)
        self.channel_send.assert_not_awaited()
        self.disconnect.assert_not_awaited()
