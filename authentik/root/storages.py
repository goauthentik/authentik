"""authentik storage backends"""

import os

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
        url = self.bucket.meta.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expire,
            HttpMethod=http_method,
        )

        if self.custom_domain:
            # Key parameter can't be empty. Use "/" and remove it later.
            params["Key"] = "/"
            root_url_signed = self.bucket.meta.client.generate_presigned_url(
                "get_object", Params=params, ExpiresIn=expire
            )
            # Remove signing parameter and previously added key "/".
            root_url = self._strip_signing_parameters(root_url_signed)[:-1]
            # Replace bucket domain with custom domain.
            custom_url = f"{self.url_protocol}//{self.custom_domain}/"
            url = url.replace(root_url, custom_url)

        if self.querystring_auth:
            return url
        return self._strip_signing_parameters(url)
