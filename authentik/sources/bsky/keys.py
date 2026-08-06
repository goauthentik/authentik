import json
import time
from base64 import urlsafe_b64encode
from hashlib import sha256
from typing import TYPE_CHECKING, Any

import jwt
from django.http import HttpRequest
from jwcrypto.jwk import JWK

from authentik.lib.generators import generate_id
from authentik.providers.oauth2.dpop import DPOP_JWT_TYPE, canonical_public_jwk, jwk_thumbprint

if TYPE_CHECKING:
    from authentik.sources.bsky.models import BskySource


def generate_bsky_signing_key() -> str:
    key = JWK.generate(kty="EC", crv="P-256")
    return key.export_to_pem(private_key=True, password=None).decode()


def public_jwk(source: BskySource) -> dict[str, Any]:
    key = JWK.from_pem(source.signing_key.encode())
    return canonical_public_jwk(json.loads(key.export_public()))


def sign_client_assertion(source: BskySource, request: HttpRequest, audience: str) -> str:
    client_id = source.client_id(request)
    now = int(time.time())
    claims = {
        "iss": client_id,
        "sub": client_id,
        "aud": audience,
        "jti": generate_id(),
        "iat": now,
        "exp": now + 60,
    }
    kid = jwk_thumbprint(public_jwk(source))
    return jwt.encode(claims, source.signing_key, algorithm="ES256", headers={"kid": kid})


def sign_dpop_proof(
    source: BskySource,
    htm: str,
    htu: str,
    nonce: str | None = None,
    access_token: str | None = None,
) -> str:
    now = int(time.time())
    claims = {
        "htm": htm,
        "htu": htu,
        "iat": now,
        "jti": generate_id(),
    }
    if nonce:
        claims["nonce"] = nonce
    if access_token:
        claims["ath"] = (
            urlsafe_b64encode(sha256(access_token.encode()).digest()).rstrip(b"=").decode()
        )
    headers = {
        "typ": DPOP_JWT_TYPE,
        "jwk": public_jwk(source),
    }
    return jwt.encode(claims, source.signing_key, algorithm="ES256", headers=headers)
