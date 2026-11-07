"""Deterministic interleavings at the cache and resolution boundaries."""

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from django.test import TestCase

from authentik.enterprise.providers.oauth2_cimd.errors import MetadataUnavailable
from authentik.enterprise.providers.oauth2_cimd.jwks import ClientKeySet
from authentik.enterprise.providers.oauth2_cimd.metadata import validate_metadata
from authentik.enterprise.providers.oauth2_cimd.negotiation import MANAGED_PROFILE, PUBLIC_PROFILE
from authentik.enterprise.providers.oauth2_cimd.service import Kind, _Flight
from authentik.enterprise.providers.oauth2_cimd.tests.test_service import wait_for_waiters
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    JWKS_URI,
    json_response,
    make_service,
    managed_document,
    new_cache,
    public_document,
    public_jwk,
)


class TestResolutionRaces(TestCase):
    """No result may escape its generation or combined freshness window."""

    def test_post_invalidation_request_does_not_join_old_flight(self):
        service, transport, _ = make_service({CLIENT_ID: json_response(public_document())})
        fetched = threading.Event()
        release = threading.Event()
        original_fetch = service._fetcher.fetch

        def fetch(url, **kwargs):
            response = original_fetch(url, **kwargs)
            if not fetched.is_set():
                fetched.set()
                if not release.wait(5):
                    raise AssertionError("Old fetch was not released")
            return response

        with (
            patch.object(service._fetcher, "fetch", side_effect=fetch),
            ThreadPoolExecutor(3) as pool,
        ):
            leader = pool.submit(service.resolve, CLIENT_ID, PUBLIC_PROFILE)
            try:
                self.assertTrue(fetched.wait(5))
                waiter = pool.submit(service.resolve, CLIENT_ID, PUBLIC_PROFILE)
                wait_for_waiters(service, 1)
                service.invalidate(CLIENT_ID)
                transport.add(CLIENT_ID, json_response(public_document(client_name="Replacement")))
                replacement = pool.submit(service.resolve, CLIENT_ID, PUBLIC_PROFILE).result(5)
                self.assertEqual(replacement.metadata.client_name, "Replacement")
            finally:
                release.set()
            for future in (leader, waiter):
                with self.assertRaises(MetadataUnavailable) as ctx:
                    future.result(5)
                self.assertEqual(ctx.exception.code, "invalidated")
        self.assertEqual(
            service.resolve(CLIENT_ID, PUBLIC_PROFILE).metadata.client_name, "Replacement"
        )
        self.assertEqual(len(transport.requests), 2)

    def test_invalidated_resolved_keys_are_not_used(self):
        old_key = public_jwk("EC", 0, kid="same-id")
        new_key = public_jwk("EC", 1, kid="same-id")
        service, transport, _ = make_service(
            {CLIENT_ID: json_response(managed_document(jwks_uri=None, jwks={"keys": [old_key]}))}
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        original = service.find_signing_key(resolved, "same-id")
        service.invalidate(CLIENT_ID)
        transport.add(
            CLIENT_ID,
            json_response(managed_document(jwks_uri=None, jwks={"keys": [new_key]})),
        )
        replacement = service.find_signing_key(resolved, "same-id")
        self.assertNotEqual(original, replacement)
        self.assertEqual(len(transport.requests), 2)

    def test_invalidation_during_cached_metadata_validation(self):
        service, _, _ = make_service({CLIENT_ID: json_response(public_document())})
        service.get_metadata(CLIENT_ID)

        def validate(document, client_id):
            result = validate_metadata(document, client_id)
            service.invalidate(client_id)
            return result

        with patch(
            "authentik.enterprise.providers.oauth2_cimd.service.validate_metadata", validate
        ):
            with self.assertRaises(MetadataUnavailable) as ctx:
                service.get_metadata(CLIENT_ID)
        self.assertEqual(ctx.exception.code, "invalidated")

    def test_invalidation_during_key_selection(self):
        service, _, _ = make_service(
            {
                CLIENT_ID: json_response(
                    managed_document(jwks_uri=None, jwks={"keys": [public_jwk("EC", kid="a")]})
                )
            }
        )
        resolved = service.resolve(CLIENT_ID, MANAGED_PROFILE)
        original_find = ClientKeySet.find

        def find(keys, kid):
            result = original_find(keys, kid)
            service.invalidate(CLIENT_ID)
            return result

        with patch.object(ClientKeySet, "find", find):
            with self.assertRaises(MetadataUnavailable) as ctx:
                service.find_signing_key(resolved, "a")
        self.assertEqual(ctx.exception.code, "invalidated")

    def test_metadata_generation_pins_remote_keys(self):
        service, transport, _ = make_service({CLIENT_ID: json_response(managed_document())})
        cached = service.get_metadata(CLIENT_ID)
        service.invalidate(CLIENT_ID)
        with self.assertRaises(MetadataUnavailable) as ctx:
            service.get_keys(cached)
        self.assertEqual(ctx.exception.code, "invalidated")
        self.assertEqual(len(transport.requests), 1)

    def test_metadata_expires_while_fetching_keys(self):
        keys_response = json_response({"keys": [public_jwk("EC", kid="a")]})
        keys_response.chunk_delay = 2
        service, _, clock = make_service(
            {
                CLIENT_ID: json_response(managed_document()),
                JWKS_URI: keys_response,
            }
        )
        service.get_metadata(CLIENT_ID)
        clock.advance(119)
        with self.assertRaises(MetadataUnavailable) as ctx:
            service.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertEqual(ctx.exception.code, "expired")

    def test_invalidation_after_keys_before_return(self):
        service, _, _ = make_service(
            {
                CLIENT_ID: json_response(managed_document()),
                JWKS_URI: json_response({"keys": [public_jwk("EC", kid="a")]}),
            }
        )
        original_get_keys = service.get_keys

        def get_keys(*args, **kwargs):
            keys = original_get_keys(*args, **kwargs)
            service.invalidate(CLIENT_ID)
            return keys

        with patch.object(service, "get_keys", side_effect=get_keys):
            with self.assertRaises(MetadataUnavailable) as ctx:
                service.resolve(CLIENT_ID, MANAGED_PROFILE)
        self.assertEqual(ctx.exception.code, "invalidated")

    def test_response_delay_reaches_freshness(self):
        response = json_response(public_document(), cache_control="max-age=300")
        response.header_delay = 2
        service, _, clock = make_service({CLIENT_ID: response})
        resolved = service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(resolved.expires_at - clock(), 298)


class TestSharedLockRaces(TestCase):
    """A cache observation made before lock acquisition is not authoritative."""

    def test_post_lock_recheck(self):
        for forced in (False, True):
            with self.subTest(forced=forced):
                shared = new_cache()
                responses = {CLIENT_ID: json_response(public_document())}
                leader, leader_transport, _ = make_service(responses, shared_cache=shared)
                follower, follower_transport, _ = make_service(responses, shared_cache=shared)
                if forced:
                    leader.get_metadata(CLIENT_ID)
                original_add = follower._add

                def add(*args, leader=leader, forced=forced, original_add=original_add, **kwargs):
                    leader.get_metadata(CLIENT_ID, force=forced)
                    return original_add(*args, **kwargs)

                with patch.object(follower, "_add", side_effect=add):
                    follower.get_metadata(CLIENT_ID, force=forced)
                self.assertEqual(follower_transport.requests, [])
                self.assertEqual(len(leader_transport.requests), 2 if forced else 1)

    def test_generation_rechecked_after_lock(self):
        service, transport, _ = make_service({CLIENT_ID: json_response(public_document())})
        original_add = service._add

        def add(*args, **kwargs):
            result = original_add(*args, **kwargs)
            service.invalidate(CLIENT_ID)
            return result

        with patch.object(service, "_add", side_effect=add):
            with self.assertRaises(MetadataUnavailable) as ctx:
                service.resolve(CLIENT_ID, PUBLIC_PROFILE)
        self.assertEqual(ctx.exception.code, "invalidated")
        self.assertEqual(transport.requests, [])

    def test_known_refreshed_key_bypasses_throttle(self):
        for inline in (False, True):
            with self.subTest(inline=inline):
                old_keys = {"keys": [public_jwk("EC", 0, kid="a")]}
                new_keys = {"keys": [public_jwk("EC", 1, kid="b")]}
                old_document = (
                    managed_document(jwks_uri=None, jwks=old_keys) if inline else managed_document()
                )
                shared = new_cache()
                responses = {
                    CLIENT_ID: json_response(old_document),
                    JWKS_URI: json_response(old_keys),
                }
                leader, transport, _ = make_service(responses, shared_cache=shared)
                follower, follower_transport, _ = make_service(responses, shared_cache=shared)
                snapshot = follower.resolve(CLIENT_ID, MANAGED_PROFILE)
                url = CLIENT_ID if inline else JWKS_URI
                document = managed_document(jwks_uri=None, jwks=new_keys) if inline else new_keys
                transport.add(url, json_response(document))
                self.assertEqual(leader.find_signing_key(snapshot, "b").kid, "b")
                requests = len(follower_transport.requests)
                self.assertEqual(follower.find_signing_key(snapshot, "b").kid, "b")
                self.assertEqual(len(follower_transport.requests), requests)

    def test_unknown_key_waits_for_active_refresh(self):
        shared = new_cache()
        responses = {
            CLIENT_ID: json_response(managed_document()),
            JWKS_URI: json_response({"keys": [public_jwk("EC", 0, kid="a")]}),
        }
        leader, transport, _ = make_service(responses, shared_cache=shared)
        follower, follower_transport, _ = make_service(responses, shared_cache=shared)
        snapshot = leader.resolve(CLIENT_ID, MANAGED_PROFILE)
        transport.add(JWKS_URI, json_response({"keys": [public_jwk("EC", 1, kid="b")]}))
        started = threading.Event()
        release = threading.Event()
        original_fetch = leader._fetcher.fetch

        def fetch(*args, **kwargs):
            started.set()
            if not release.wait(5):
                raise AssertionError("Refresh was not released")
            return original_fetch(*args, **kwargs)

        with (
            patch.object(leader._fetcher, "fetch", side_effect=fetch),
            ThreadPoolExecutor(1) as pool,
        ):
            refreshed = pool.submit(leader.find_signing_key, snapshot, "b")
            try:
                self.assertTrue(started.wait(5))

                def poll(_seconds):
                    release.set()
                    self.assertEqual(refreshed.result(5).kid, "b")

                follower._sleep = poll
                self.assertEqual(follower.find_signing_key(snapshot, "b").kid, "b")
            finally:
                release.set()
        self.assertEqual(len(transport.requests), 3)
        self.assertEqual(follower_transport.requests, [])

    def test_flight_waiter_rechecks_generation(self):
        service, _, _ = make_service({CLIENT_ID: json_response(public_document())})
        entry_key = service._entry_key(Kind.METADATA, CLIENT_ID)
        service.get_metadata(CLIENT_ID)
        entry, generation = service._lookup(Kind.METADATA, CLIENT_ID, entry_key)
        flight = _Flight()
        flight.result = entry
        service._flights[(entry_key, generation, None)] = flight

        def wait(_timeout):
            service.invalidate(CLIENT_ID)
            return True

        with patch.object(flight.done, "wait", side_effect=wait):
            with self.assertRaises(MetadataUnavailable) as ctx:
                service._load(Kind.METADATA, CLIENT_ID, CLIENT_ID, entry_key, "0", newer_than=None)
        self.assertEqual(ctx.exception.code, "invalidated")
