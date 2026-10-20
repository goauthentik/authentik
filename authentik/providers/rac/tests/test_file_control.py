"""RAC file control remains session-bound and contains no file bytes."""

import asyncio
import json
from hashlib import sha256
from hmac import new
from time import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import connection as db_connection
from django.test import SimpleTestCase, override_settings
from django.test.client import RequestFactory

from authentik.lib.config import CONFIG
from authentik.providers.rac.api.files import FileListQuerySerializer, query_directory
from authentik.providers.rac.api.transfers import (
    TransferCreateSerializer,
    identity_for,
    transfer_key,
)
from authentik.providers.rac.bulk_auth import authorize_bulk
from authentik.providers.rac.consumer_client import RACClientConsumer
from authentik.providers.rac.control import connection_key


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}},
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class TestFileControl(SimpleTestCase):
    async def test_list_uses_live_connection_without_consumed_token_row(self):
        layer = get_channel_layer()
        owner = RACClientConsumer()
        owner.channel_layer = layer
        owner.channel_name = await layer.new_channel()
        owner.dest_channel_id = await layer.new_channel()
        owner.connection_id = str(uuid4())
        owner.rac_token = "consumed-token"
        owner.connection_protocol = "rdp"
        owner.connection_settings = {"enable-drive": "true"}
        owner.token = SimpleNamespace(is_expired=False)
        owner.stream_identity = {"user": "1", "session": "session", "tenant": "public"}
        owner.control_requests = {}
        owner.bulk_requests = {}
        owner.bulk_transfers = set()
        key = connection_key("public", owner.rac_token, owner.connection_id)
        await cache.aset(
            key,
            {
                **owner.stream_identity,
                "channel": owner.channel_name,
                "protocol": "rdp",
                "drive": True,
                "outpost_user": "2",
            },
        )

        async def dispatch():
            while True:
                event = await layer.receive(owner.channel_name)
                await getattr(owner, event["type"].replace(".", "_"))(event)

        async def outpost():
            event = await layer.receive(owner.dest_channel_id)
            self.assertEqual(event["type"], "event.file.list")
            payload = json.loads(event["payload"])
            self.assertEqual(payload["path"], "/folder")
            self.assertNotIn("data", payload)
            await layer.send(
                owner.channel_name,
                {
                    "type": "event.file.list.reply",
                    "outpost_channel": owner.dest_channel_id,
                    "payload": {
                        "request": payload["request"],
                        "status": 200,
                        "entries": [
                            {"name": "empty", "path": "/folder/empty", "kind": "file", "size": 0}
                        ],
                        "cursor": "",
                    },
                },
            )

        tasks = [asyncio.create_task(dispatch()), asyncio.create_task(outpost())]
        try:
            data = {"token": owner.rac_token, "connection": owner.connection_id, "path": "/folder"}
            result = await query_directory(dict(owner.stream_identity), data)
            self.assertEqual(result["entries"][0]["size"], 0)
            wrong = {**owner.stream_identity, "tenant": "other"}
            self.assertEqual((await query_directory(wrong, data))["status"], 404)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            await cache.aclear()
            await layer.flush()

    def test_virtual_paths_and_upload_size(self):
        base = {"token": "t", "connection": str(uuid4()), "direction": "upload", "size": 0}
        for path in ["/../x", "/a//b", "/a\\b", "/", "relative"]:
            self.assertFalse(TransferCreateSerializer(data={**base, "path": path}).is_valid())
        self.assertTrue(TransferCreateSerializer(data={**base, "path": "/empty"}).is_valid())
        self.assertFalse(
            TransferCreateSerializer(
                data={k: v for k, v in {**base, "path": "/x"}.items() if k != "size"}
            ).is_valid()
        )
        self.assertFalse(
            FileListQuerySerializer(
                data={"token": "t", "connection": str(uuid4()), "path": "/", "cursor": "../x"}
            ).is_valid()
        )

    async def test_terminal_control_releases_transfer_without_file_bytes(self):
        owner = RACClientConsumer()
        owner.dest_channel_id = "outpost-channel"
        owner.stream_disconnected = False
        owner.bulk_transfers = {"transfer-id"}
        owner.bulk_requests = {}
        owner.control_requests = {}
        owner.send = AsyncMock()
        await cache.aset("rac-bulk/transfer-id", {"prepared": True})
        await cache.aset("rac-bulk-owner/transfer-id", {"instance": "server-a"})
        await owner.event_file_bulk_reply(
            {
                "outpost_channel": "outpost-channel",
                "payload": {"request": "", "id": "transfer-id", "status": 200},
            }
        )
        self.assertEqual(owner.bulk_transfers, set())
        self.assertIsNone(await cache.aget("rac-bulk/transfer-id"))
        self.assertIsNone(await cache.aget("rac-bulk-owner/transfer-id"))
        self.assertIn("authentik-bulk", owner.send.await_args.kwargs["text_data"])
        self.assertNotIn("data", owner.send.await_args.kwargs["text_data"])

    def test_list_api_requires_csrf(self):
        from django.conf import settings
        from django.middleware.csrf import get_token
        from rest_framework.authentication import SessionAuthentication
        from rest_framework.test import APIRequestFactory

        from authentik.providers.rac.api.files import ConnectionFileViewSet

        factory = APIRequestFactory(enforce_csrf_checks=True)
        view = ConnectionFileViewSet.as_view(
            {"post": "list_files"}, authentication_classes=[SessionAuthentication]
        )
        payload = {"token": "t", "connection": str(uuid4()), "path": "/"}

        def request():
            req = factory.post("/api/v3/rac/files/list/", payload, format="json")
            req.user = SimpleNamespace(pk=1, is_authenticated=True, is_active=True)
            req.session = SimpleNamespace(session_key="session")
            return req

        with (
            patch(
                "authentik.providers.rac.api.files.query_directory",
                new=AsyncMock(return_value={"status": 200, "entries": [], "cursor": ""}),
            ),
            patch("authentik.providers.rac.api.files.session_active", return_value=True),
        ):
            self.assertEqual(view(request()).status_code, 403)
            req = request()
            req.META[settings.CSRF_HEADER_NAME] = get_token(req)
            req.COOKIES[settings.CSRF_COOKIE_NAME] = req.META["CSRF_COOKIE"]
            self.assertEqual(view(req).status_code, 200)

    def test_bulk_authorization_binds_outpost_session_and_csrf(self):
        self.assert_bulk_authorization()

    def assert_bulk_authorization(self):
        from django.conf import settings
        from django.middleware.csrf import get_token

        identifier = uuid4()
        key = str(identifier)
        transfer = {
            "user": "1",
            "session": "session",
            "tenant": db_connection.schema_name,
            "token": "consumed-token",
            "connection": str(uuid4()),
            "direction": "upload",
            "path": "/data.bin",
            "size": 4,
            "outpost_user": "2",
            "prepared": True,
        }
        cache.set(transfer_key(key), transfer, timeout=90)
        timestamp = str(int(time()))
        instance = "server-a"
        address = "http://server-a:9823"

        def signed(operation: str, tenant: str | None = None) -> dict:
            tenant = (tenant or db_connection.schema_name) if operation == "outpost" else ""
            payload = f"{key}:{operation}:{timestamp}:{instance}:{address}:{tenant}".encode()
            headers = {
                "HTTP_X_RAC_TIME": timestamp,
                "HTTP_X_RAC_OPERATION": operation,
                "HTTP_X_RAC_INSTANCE": instance,
                "HTTP_X_RAC_ADDRESS": address,
                "HTTP_X_RAC_SIGNATURE": new(
                    settings.SECRET_KEY.encode(), payload, sha256
                ).hexdigest(),
            }
            if tenant:
                headers["HTTP_X_RAC_TENANT"] = tenant
            return headers

        factory = RequestFactory(enforce_csrf_checks=True)
        url = f"/if/rac/bulk/{key}/authorize/"
        with patch(
            "authentik.providers.rac.bulk_auth.TokenAuthentication.authenticate",
            return_value=(SimpleNamespace(pk=2), None),
        ):
            forged = factory.get(url, **{**signed("outpost"), "HTTP_X_RAC_TENANT": "other"})
            self.assertEqual(authorize_bulk(forged, identifier).status_code, 403)
            wrong_namespace = factory.get(url, **signed("outpost", "other"))
            self.assertEqual(authorize_bulk(wrong_namespace, identifier).status_code, 403)
            outpost = factory.get(url, **signed("outpost"))
            self.assertEqual(authorize_bulk(outpost, identifier).status_code, 200)
            transfer["tenant"] = "other"
            cache.set(transfer_key(key), transfer, timeout=90)
            self.assertEqual(authorize_bulk(outpost, identifier).status_code, 404)
            transfer["tenant"] = db_connection.schema_name
            cache.set(transfer_key(key), transfer, timeout=90)
        browser = factory.post(url, **signed("upload"))
        browser.user = SimpleNamespace(pk=1, is_authenticated=True)
        browser.session = SimpleNamespace(session_key="session")
        with (
            patch("authentik.providers.rac.bulk_auth.session_active", return_value=True),
            patch(
                "authentik.providers.rac.bulk_auth.connection_record",
                return_value={"outpost_user": "2", "upload": True},
            ) as connection,
        ):
            self.assertEqual(authorize_bulk(browser, identifier).status_code, 403)
            browser.META[settings.CSRF_HEADER_NAME] = get_token(browser)
            browser.COOKIES[settings.CSRF_COOKIE_NAME] = browser.META["CSRF_COOKIE"]
            self.assertEqual(authorize_bulk(browser, identifier).status_code, 200)
            connection.return_value = {"outpost_user": "2", "upload": False}
            self.assertEqual(authorize_bulk(browser, identifier).status_code, 404)
            connection.return_value = {"outpost_user": "2", "upload": True}
            browser.user = SimpleNamespace(pk=3, is_authenticated=True)
            self.assertEqual(authorize_bulk(browser, identifier).status_code, 404)
            browser.user = SimpleNamespace(pk=1, is_authenticated=True)
            connection.return_value = None
            self.assertEqual(authorize_bulk(browser, identifier).status_code, 404)
        cache.clear()

    def test_transfer_api_keeps_original_direction_policy_and_session_identity(self):
        from django.conf import settings
        from django.middleware.csrf import get_token
        from rest_framework.authentication import SessionAuthentication
        from rest_framework.test import APIRequestFactory

        from authentik.providers.rac.api.transfers import FileTransferViewSet

        token = "consumed-token"
        connection = str(uuid4())
        record = {
            "user": "1",
            "session": "session",
            "tenant": db_connection.schema_name,
            "channel": "owner-channel",
            "protocol": "rdp",
            "drive": True,
            "outpost_user": "2",
            "upload": False,
            "download": True,
        }
        cache.set(connection_key(record["tenant"], token, connection), record)
        factory = APIRequestFactory(enforce_csrf_checks=True)
        create = FileTransferViewSet.as_view(
            {"post": "create"}, authentication_classes=[SessionAuthentication]
        )
        destroy = FileTransferViewSet.as_view(
            {"delete": "destroy"}, authentication_classes=[SessionAuthentication]
        )

        def browser(method: str, user: int = 1):
            payload = {
                "token": token,
                "connection": connection,
                "direction": "upload",
                "path": "/data.bin",
                "size": 0,
            }
            req = getattr(factory, method)("/api/v3/rac/file_transfers/", payload, format="json")
            req.user = SimpleNamespace(pk=user, is_authenticated=True, is_active=True)
            req.session = SimpleNamespace(session_key="session")
            req.META[settings.CSRF_HEADER_NAME] = get_token(req)
            req.COOKIES[settings.CSRF_COOKIE_NAME] = req.META["CSRF_COOKIE"]
            return req

        with (
            patch("authentik.providers.rac.api.transfers.session_active", return_value=True),
            patch(
                "authentik.providers.rac.api.transfers.control",
                new=AsyncMock(return_value={"status": 200, "size": 0}),
            ) as control,
        ):
            self.assertEqual(create(browser("post")).status_code, 403)
            control.assert_not_awaited()
            record["upload"] = True
            cache.set(connection_key(record["tenant"], token, connection), record)
            response = create(browser("post"))
            self.assertEqual(response.status_code, 201)
            identifier = response.data["id"]
            self.assertEqual(destroy(browser("delete", user=3), pk=identifier).status_code, 404)
            self.assertEqual(destroy(browser("delete"), pk=identifier).status_code, 200)
            self.assertIsNone(cache.get(transfer_key(identifier)))
        cache.clear()

    def test_configured_schema_without_tenant_middleware(self):
        """HTTP identity and signed outpost requests share the configured schema."""
        configured_get = CONFIG.get

        def nondefault_schema(key, *args, **kwargs):
            if key == "postgresql.default_schema":
                return "rac_custom"
            return configured_get(key, *args, **kwargs)

        request = RequestFactory().get("/api/v3/rac/files/list/")
        request.user = SimpleNamespace(pk=1)
        request.session = SimpleNamespace(session_key="session")
        with patch.object(CONFIG, "get", side_effect=nondefault_schema):
            self.assertEqual(
                identity_for(request),
                {"user": "1", "session": "session", "tenant": "rac_custom"},
            )
            self.assert_bulk_authorization()
