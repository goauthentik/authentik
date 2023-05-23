"""OCI Client"""
from typing import Any
from urllib.parse import ParseResult, urlparse

from opencontainers.distribution.reggie import (
    NewClient,
    WithDebug,
    WithDefaultName,
    WithDigest,
    WithReference,
    WithUserAgent,
    WithUsernamePassword,
)
from requests.exceptions import RequestException
from structlog import get_logger
from structlog.stdlib import BoundLogger

from authentik.lib.sentry import SentryIgnoredException
from authentik.lib.utils.http import authentik_user_agent

OCI_MEDIA_TYPE = "application/vnd.goauthentik.blueprint.v1+yaml"


class OCIException(SentryIgnoredException):
    """OCI-related errors"""


class BlueprintOCIClient:
    """Blueprint OCI Client"""

    url: ParseResult
    sanitized_url: str
    logger: BoundLogger
    ref: str
    client: NewClient

    def __init__(self, url: str) -> None:
        self._parse_url(url)
        self.logger = get_logger().bind(url=self.sanitized_url)

        self.ref = "latest"
        # Remove the leading slash of the path to convert it to an image name
        path = self.url.path[1:]
        if ":" in path:
            # if there's a colon in the path, use everything after it as a ref
            path, _, self.ref = path.partition(":")
        base_url = f"https://{self.url.hostname}"
        if self.url.port:
            base_url += f":{self.url.port}"
        self.client = NewClient(
            base_url,
            WithUserAgent(authentik_user_agent()),
            WithUsernamePassword(self.url.username, self.url.password),
            WithDefaultName(path),
            WithDebug(True),
        )

    def _parse_url(self, url: str):
        self.url = urlparse(url)
        netloc = self.url.netloc
        if "@" in netloc:
            netloc = netloc[netloc.index("@") + 1 :]
        self.sanitized_url = self.url._replace(netloc=netloc).geturl()

    def fetch_manifests(self) -> dict[str, Any]:
        """Fetch manifests for ref"""
        self.logger.info("Fetching OCI manifests for blueprint")
        manifest_request = self.client.NewRequest(
            "GET",
            "/v2/<name>/manifests/<reference>",
            WithReference(self.ref),
        ).SetHeader("Accept", "application/vnd.oci.image.manifest.v1+json")
        try:
            manifest_response = self.client.Do(manifest_request)
            manifest_response.raise_for_status()
        except RequestException as exc:
            raise OCIException(exc) from exc
        manifest = manifest_response.json()
        if "errors" in manifest:
            raise OCIException(manifest["errors"])
        return manifest

    def fetch_blobs(self, manifest: dict[str, Any]):
        """Fetch blob based on manifest info"""
        blob = None
        for layer in manifest.get("layers", []):
            if layer.get("mediaType", "") == OCI_MEDIA_TYPE:
                blob = layer.get("digest")
                self.logger.debug("Found layer with matching media type", blob=blob)
        if not blob:
            raise OCIException("Blob not found")

        blob_request = self.client.NewRequest(
            "GET",
            "/v2/<name>/blobs/<digest>",
            WithDigest(blob),
        )
        try:
            blob_response = self.client.Do(blob_request)
            blob_response.raise_for_status()
            return blob_response.text
        except RequestException as exc:
            raise OCIException(exc) from exc
