"""authentik storage backends"""

import os
from urllib.parse import parse_qsl, urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files.storage import FileSystemStorage
from django.db import connection
from storages.backends.s3 import S3Storage as BaseS3Storage
from storages.utils import clean_name, safe_join

from authentik.lib.config import CONFIG


class FileStorage(FileSystemStorage):
    """File storage backend"""

    @property
    def base_location(self):
        return os.path.join(
            self._value_or_setting(self._location, settings.MEDIA_ROOT), connection.schema_name
        )

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        if self._base_url is not None and not self._base_url.endswith("/"):
            self._base_url += "/"
        return f"{self._base_url}/{connection.schema_name}/"


class S3Storage(BaseS3Storage):
    """S3 storage backend"""

    @property
    def session_profile(self) -> str | None:
        """Get session profile"""
        return CONFIG.refresh("storage.media.s3.session_profile", None)

    @session_profile.setter
    def session_profile(self, value: str):
        pass

    @property
    def access_key(self) -> str | None:
        """Get access key"""
        return CONFIG.refresh("storage.media.s3.access_key", None)

    @access_key.setter
    def access_key(self, value: str):
        pass

    @property
    def secret_key(self) -> str | None:
        """Get secret key"""
        return CONFIG.refresh("storage.media.s3.secret_key", None)

    @secret_key.setter
    def secret_key(self, value: str):
        pass

    @property
    def security_token(self) -> str | None:
        """Get security token"""
        return CONFIG.refresh("storage.media.s3.security_token", None)

    @security_token.setter
    def security_token(self, value: str):
        pass

    @property
    def secure_urls(self) -> bool:
        """Get secure_urls"""
        return CONFIG.get_bool("storage.media.s3.secure_urls", True)

    @secure_urls.setter
    def secure_urls(self, value: bool):
        pass

    def _normalize_name(self, name):
        try:
            return safe_join(self.location, connection.schema_name, name)
        except ValueError:
            raise SuspiciousOperation(f"Attempted access to '{name}' denied.") from None

    # This is a fix for https://github.com/jschneier/django-storages/pull/839
    def url(self, name, parameters=None, expire=None, http_method=None):
        # Preserve the trailing slash after normalizing the path.
        name = self._normalize_name(clean_name(name))
        params = parameters.copy() if parameters else {}
        if expire is None:
            expire = self.querystring_expire

        params["Bucket"] = self.bucket.name
        params["Key"] = name

        # Get the client and configure endpoint URL if custom_domain is set
        client = self.bucket.meta.client

        # Save original endpoint URL if we need to restore it
        original_endpoint_url = getattr(client.meta, "endpoint_url", None)

        custom_domain = self.custom_domain
        if custom_domain:
            # If the custom domain is an IDN, it needs to be punycode encoded.
            custom_domain = custom_domain.encode("idna").decode("ascii")

        try:
            # If custom domain is set, configure the endpoint URL
            if custom_domain:
                scheme = "https" if self.secure_urls else "http"
                custom_endpoint = f"{scheme}://{custom_domain}"

                # Set the endpoint URL temporarily for this request
                client.meta.endpoint_url = custom_endpoint

            # Generate the presigned URL using the correctly configured client
            url = client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expire,
                HttpMethod=http_method,
            )

            # If using custom domain, we need to handle the path correctly
            if custom_domain and self.bucket.name in url:
                # Parse the generated URL
                split_url = urlsplit(url)

                # Get the path from the S3 URL
                s3_path = split_url.path

                # Remove the leading bucket name from the path if it's present
                bucket_prefix = f"/{self.bucket.name}"
                if s3_path.startswith(bucket_prefix):
                    final_path = s3_path[len(bucket_prefix) :]
                else:
                    final_path = s3_path

                # Create the custom domain URL with the corrected path and query parameters
                url = urlunsplit(
                    (
                        scheme,
                        custom_domain,
                        final_path,
                        split_url.query,
                        split_url.fragment,
                    )
                )

        finally:
            # Restore the original endpoint URL if we changed it
            if custom_domain:
                client.meta.endpoint_url = original_endpoint_url

        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)

    def _strip_signing_parameters(self, url):
        # Boto3 does not currently support generating URLs that are unsigned. Instead
        # we take the signed URLs and strip any querystring params related to signing
        # and expiration.
        # Note that this may end up with URLs that are still invalid, especially if
        # params are passed in that only work with signed URLs, e.g. response header
        # params.
        # The code attempts to strip all query parameters that match names of known
        # parameters from v2 and v4 signatures, regardless of the actual signature
        # version used.
        split_url = urlsplit(url)
        qs = parse_qsl(split_url.query, keep_blank_values=True)
        blacklist = {
            "x-amz-algorithm",
            "x-amz-credential",
            "x-amz-date",
            "x-amz-expires",
            "x-amz-signedheaders",
            "x-amz-signature",
            "x-amz-security-token",
            "awsaccesskeyid",
            "expires",
            "signature",
        }
        filtered_qs = ((key, val) for key, val in qs if key.lower() not in blacklist)
        # Note: Parameters that did not have a value in the original query string will
        # have an '=' sign appended to it, e.g ?foo&bar becomes ?foo=&bar=
        joined_qs = ("=".join(keyval) for keyval in filtered_qs)
        split_url = split_url._replace(query="&".join(joined_qs))
        return split_url.geturl()
