"""Local Rust authorization hook; no file bytes pass through Django."""

from hashlib import sha256
from hmac import compare_digest, new
from time import time
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import AuthenticationFailed

from authentik.api.authentication import TokenAuthentication
from authentik.providers.rac.api.transfers import (
    connection_record,
    identity_for,
    session_active,
    transfer_key,
)

SIGNATURE_TOLERANCE_SECONDS = 30


def owner_key(identifier: str) -> str:
    return f"rac-bulk-owner/{identifier}"


def valid_internal_signature(request: HttpRequest, identifier: str) -> bool:
    timestamp = request.headers.get("X-RAC-Time", "")
    operation = request.headers.get("X-RAC-Operation", "")
    instance = request.headers.get("X-RAC-Instance", "")
    address = request.headers.get("X-RAC-Address", "")
    try:
        if abs(time() - int(timestamp)) > SIGNATURE_TOLERANCE_SECONDS:
            return False
    except ValueError:
        return False
    if operation not in {"outpost", "upload", "download", "poll"}:
        return False
    tenant = request.headers.get("X-RAC-Tenant", "") if operation == "outpost" else ""
    message = f"{identifier}:{operation}:{timestamp}:{instance}:{address}:{tenant}".encode()
    expected = new(settings.SECRET_KEY.encode(), message, sha256).hexdigest()
    return compare_digest(request.headers.get("X-RAC-Signature", ""), expected)


@csrf_protect
def authorize_bulk(request: HttpRequest, identifier: UUID) -> HttpResponse:
    """Verify the browser session or Outpost bearer before Rust touches content."""
    key = str(identifier)
    if not valid_internal_signature(request, key):
        return HttpResponse(status=403)
    operation = request.headers["X-RAC-Operation"]
    if operation == "outpost":
        tenant = request.headers.get("X-RAC-Tenant", "")
        if tenant != connection.schema_name:
            return HttpResponse(status=403)
    return _authorize_transfer(request, key, operation)


def _authorize_transfer(  # noqa: PLR0911
    request: HttpRequest, key: str, operation: str
) -> HttpResponse:
    transfer = cache.get(transfer_key(key))
    if not transfer:
        return HttpResponse(status=404)
    if not transfer.get("prepared"):
        return HttpResponse(status=503)
    if operation == "outpost":
        if transfer.get("tenant") != connection.schema_name:
            return HttpResponse(status=404)
        try:
            authenticated = TokenAuthentication().authenticate(request)
        except AuthenticationFailed:
            return HttpResponse(status=403)
        if not authenticated or str(authenticated[0].pk) != transfer["outpost_user"]:
            return HttpResponse(status=403)
    else:
        if not request.user.is_authenticated or not session_active(request):
            return HttpResponse(status=404)
        identity = identity_for(request)
        if any(transfer.get(field) != value for field, value in identity.items()):
            return HttpResponse(status=404)
        record = connection_record(identity, transfer["token"], UUID(transfer["connection"]))
        if (
            not record
            or record["outpost_user"] != transfer["outpost_user"]
            or not record.get(transfer["direction"])
        ):
            return HttpResponse(status=404)
        if operation not in {"poll", transfer["direction"]}:
            return HttpResponse(status=403)
    if operation == "outpost":
        owner = {
            "instance": request.headers.get("X-RAC-Instance", ""),
            "address": request.headers.get("X-RAC-Address", ""),
        }
        if not owner["instance"] or not owner["address"]:
            return HttpResponse(status=400)
        if not cache.add(owner_key(key), owner, timeout=90):
            if cache.get(owner_key(key)) != owner:
                return HttpResponse(status=409)
        transfer["owner"] = owner
        cache.set(transfer_key(key), transfer, timeout=90)
    else:
        owner = cache.get(owner_key(key))
        if not owner:
            return HttpResponse(status=503)
    return JsonResponse(
        {
            "owner": owner,
            "direction": transfer["direction"],
            "size": transfer["size"],
            "filename": transfer["path"].rsplit("/", 1)[-1],
        },
        headers={"Cache-Control": "no-store"},
    )
