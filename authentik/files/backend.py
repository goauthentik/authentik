import os
from collections.abc import Generator
from enum import Enum
from pathlib import Path
from urllib.parse import urlsplit

import boto3
from botocore.config import Config
from django.db import connection
from django.utils.functional import cached_property

from authentik.lib.config import CONFIG

MEDIA_BACKEND = CONFIG.get("storage.media.backend", "file")


class Usage(Enum):
    MEDIA = "media"


class Backend:
    def __init__(self, usage: Usage):
        self.usage = usage

    def can_manage_file(self, name: str) -> bool:
        raise NotImplementedError

    def list_files(self) -> Generator[str]:
        raise NotImplementedError

    def save_file(self, name: str, content: bytes) -> None:
        raise NotImplementedError

    def delete_file(self, name: str) -> None:
        raise NotImplementedError

    def file_url(self, name: str) -> str:
        raise NotImplementedError


class StaticBackend(Backend):
    def can_manage_file(self, name: str) -> bool:
        return name.startswith("/static") or name.startswith("web/dist/assets")

    def list_files(self) -> Generator[str]:
        for dir in ("assets/icons", "assets/images"):
            for _, _, files in Path(f"web/dist/{dir}").walk():
                for file in files:
                    if file.endswith(".svg") or file.endswith("png"):
                        yield f"/static/{dir}/{file}"
            for _, _, files in Path(f"web/dist/{dir}").walk():
                for file in files:
                    if file.startswith("flow_") or file.startswith("logo-"):
                        yield f"/static/{dir}/{file}"

    def file_url(self, name: str) -> str:
        prefix = CONFIG.get("web.path", "/")[:-1]
        if name.startswith("/static"):
            return prefix + name
        if name.startswith("web/dist/assets"):
            return f"{prefix}/static/dist/{name.removeprefix('web/dist/')}"
        raise RuntimeError


class PassthroughBackend(Backend):
    def can_manage_file(self, name: str) -> bool:
        return name.startswith("fa://") or name.startswith("http:")

    def list_files(self) -> Generator[str]:
        yield from []

    def file_url(self, name: str) -> str:
        return name


class FileBackend(Backend):
    @property
    def base_path(self) -> Path:
        return Path(CONFIG.get("storage.media.file.path")) / Path(connection.schema_name)

    def can_manage_file(self, name: str) -> bool:
        return MEDIA_BACKEND == "file"

    def list_files(self) -> Generator[str]:
        for dir, _, files in self.base_path.walk():
            for file in files:
                if file.endswith(".svg") or file.endswith("png"):
                    yield os.path.join(dir, file)

    def save_file(self, name: str, content: bytes) -> None:
        path = self.base_path / Path(name)
        with open(path, "wb") as f:
            f.write(content)

    def delete_file(self, name: str) -> None:
        path = self.base_path / Path(name)
        path.unlink(missing_ok=True)

    def file_url(self, name: str) -> str:
        prefix = CONFIG.get("web.path", "/")[:-1]
        return f"{prefix}/{self.usage.value}/{connection.schema_name}/{name}"


class S3Backend(Backend):
    @property
    def base_path(self) -> str:
        return f"{self.usage}/{connection.schema_name}/"

    @cached_property
    def bucket_name(self) -> str:
        return CONFIG.get("storage.media.s3.bucket_name")

    @cached_property
    def session(self) -> boto3.Session:
        session_profile = CONFIG.get("storage.media.s3.session_profile", None)
        if session_profile is not None:
            return boto3.Session(profile_name=session_profile)
        else:
            return boto3.Session(
                aws_access_key_id=CONFIG.get("storage.media.s3.access_key", None),
                aws_secret_access_key=CONFIG.get("storage.media.s3.secret_key", None),
                aws_session_token=CONFIG.get("storage.media.s3.security_token", None),
            )

    @cached_property
    def client(self):
        return boto3.client(
            "s3",
            # region_name=CONFIG.get("storage.media.s3.region", None),
            # use_ssl=CONFIG.get_bool("storage.media.s3.use_ssl", True),
            # endpoint_url=CONFIG.get("storage.media.s3.endpoint", None),
            # config=Config(
            #     signature_version="s3v4",
            # ),
        )

    def can_manage_file(self, name: str) -> bool:
        return MEDIA_BACKEND == "s3"

    def list_files(self) -> Generator[str]:
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.base_path)

        for page in pages:
            for obj in page.get("Contents", []):
                key = obj["Key"]
                yield key.removeprefix(self.base_path)

    def save_file(self, name: str, content: bytes) -> None:
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}/{name}",
            Body=content,
            ACL="private",
        )

    def delete_file(self, name: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.base_path}/{name}",
        )

    def file_url(self, name: str) -> str:
        http_method = "https" if CONFIG.get("storage.media.s3.secure_urls", True) else "http"
        params = {
            "Bucket": self.bucket_name,
            "Key": f"{self.base_path}/{name}",
        }
        expires_in = 3600
        url = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
            HttpMethod=http_method,
        )
        custom_domain = CONFIG.get("storage.media.s3.custom_domain", None)
        if custom_domain:
            url = urlsplit(url)
            params["Key"] = "/"
            root_url_signed = self.client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            root_url = urlsplit(root_url_signed)
            root_url = f"{root_url.scheme}://{root_url.netloc}"
            url.replace(root_url, f"{http_method}://{custom_domain}/")
        return url
