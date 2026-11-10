"""Gateway sessions for legacy (`initialize`-based) MCP clients.

The gateway stays stateless: the backends' sessions are encrypted into the single
`Mcp-Session-Id` the client presents on every request. Encryption keeps backend session
IDs from leaking to clients, and authentication binds a session to its user and gateway."""

from base64 import urlsafe_b64encode
from dataclasses import asdict
from hashlib import sha256
from json import dumps, loads

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

from authentik.enterprise.providers.mcp.client import BackendSession

SESSION_MAX_AGE = 60 * 60 * 24


def _fernet() -> Fernet:
    key = sha256(f"{settings.SECRET_KEY}:goauthentik.io/providers/mcp/session".encode()).digest()
    return Fernet(urlsafe_b64encode(key))


def encode_session(user_pk: int, gateway_pk: int, backends: dict[str, BackendSession]) -> str:
    payload = {
        "u": user_pk,
        "g": gateway_pk,
        "b": {pk: asdict(session) for pk, session in backends.items()},
    }
    return _fernet().encrypt(dumps(payload).encode()).decode()


def decode_session(
    session_id: str, user_pk: int, gateway_pk: int
) -> dict[str, BackendSession] | None:
    """Backend sessions by backend primary key, or None if the session is invalid, expired,
    or belongs to another user or gateway"""
    try:
        payload = loads(_fernet().decrypt(session_id.encode(), ttl=SESSION_MAX_AGE))
    except InvalidToken, ValueError:
        return None
    if payload.get("u") != user_pk or payload.get("g") != gateway_pk:
        return None
    return {pk: BackendSession(**session) for pk, session in payload["b"].items()}
