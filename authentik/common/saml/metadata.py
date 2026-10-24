"""Fetch Service Provider metadata from a URL"""

from django.utils.translation import gettext as _
from requests import RequestException

from authentik.lib.utils.http import get_http_session

# Metadata for a single Service Provider is a few kilobytes; cap the download so a
# misconfigured URL pointing at a large document can't exhaust memory.
METADATA_MAX_SIZE = 5 * 1024 * 1024
METADATA_TIMEOUT = 10


class MetadataFetchError(Exception):
    """Raised when metadata could not be downloaded from a URL"""


def fetch_metadata(url: str) -> str:
    """Download SAML metadata from `url` and return it as text."""
    session = get_http_session()
    try:
        response = session.get(url, timeout=METADATA_TIMEOUT, stream=True)
        response.raise_for_status()
        body = b""
        for chunk in response.iter_content(chunk_size=64 * 1024):
            body += chunk
            if len(body) > METADATA_MAX_SIZE:
                raise MetadataFetchError(_("Metadata exceeds the maximum size."))
    except RequestException as exc:
        raise MetadataFetchError(
            _("Failed to download metadata: {message}").format(message=str(exc))
        ) from exc
    return body.decode(response.encoding or "utf-8", errors="replace")
