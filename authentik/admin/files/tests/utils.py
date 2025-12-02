import shutil
from tempfile import mkdtemp

from authentik.admin.files.backends.s3 import S3Backend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG, UNSET
from authentik.lib.generators import generate_id


class FileTestFileBackendMixin:
    def setUp(self):
        self.original_media_backend = CONFIG.get("storage.media.backend", UNSET)
        self.original_media_backend_path = CONFIG.get("storage.media.file.path", UNSET)
        self.media_backend_path = mkdtemp()
        CONFIG.set("storage.media.backend", "file")
        CONFIG.set("storage.media.file.path", str(self.media_backend_path))

        self.original_reports_backend = CONFIG.get("storage.reports.backend", UNSET)
        self.original_reports_backend_path = CONFIG.get("storage.reports.file.path", UNSET)
        self.reports_backend_path = mkdtemp()
        CONFIG.set("storage.reports.backend", "file")
        CONFIG.set("storage.reports.file.path", str(self.reports_backend_path))

    def tearDown(self):
        if self.original_media_backend is not UNSET:
            CONFIG.set("storage.media.backend", self.original_media_backend)
        else:
            CONFIG.delete("storage.media.backend")
        if self.original_media_backend_path is not UNSET:
            CONFIG.set("storage.media.file.path", self.original_media_backend_path)
        else:
            CONFIG.delete("storage.media.file.path")
        shutil.rmtree(self.media_backend_path)

        if self.original_reports_backend is not UNSET:
            CONFIG.set("storage.reports.backend", self.original_reports_backend)
        else:
            CONFIG.delete("storage.reports.backend")
        if self.original_reports_backend_path is not UNSET:
            CONFIG.set("storage.reports.file.path", self.original_reports_backend_path)
        else:
            CONFIG.delete("storage.reports.file.path")
        shutil.rmtree(self.reports_backend_path)


class FileTestS3BackendMixin:
    def setUp(self):
        s3_config_keys = {
            "endpoint",
            "access_key",
            "secret_key",
            "bucket_name",
        }
        self.original_media_backend = CONFIG.get("storage.media.backend", UNSET)
        CONFIG.set("storage.media.backend", "s3")
        self.original_media_s3_settings = {}
        for key in s3_config_keys:
            self.original_media_s3_settings[key] = CONFIG.get(f"storage.media.s3.{key}", UNSET)
        self.media_s3_bucket_name = f"authentik-test-{generate_id(10)}".lower()
        CONFIG.set("storage.media.s3.endpoint", "http://localhost:8020")
        CONFIG.set("storage.media.s3.access_key", "accessKey1")
        CONFIG.set("storage.media.s3.secret_key", "secretKey1")
        CONFIG.set("storage.media.s3.bucket_name", self.media_s3_bucket_name)
        self.media_s3_backend = S3Backend(FileUsage.MEDIA)
        self.media_s3_backend.client.create_bucket(Bucket=self.media_s3_bucket_name, ACL="private")

        self.original_reports_backend = CONFIG.get("storage.reports.backend", UNSET)
        CONFIG.set("storage.reports.backend", "s3")
        self.original_reports_s3_settings = {}
        for key in s3_config_keys:
            self.original_reports_s3_settings[key] = CONFIG.get(f"storage.reports.s3.{key}", UNSET)
        self.reports_s3_bucket_name = f"authentik-test-{generate_id(10)}".lower()
        CONFIG.set("storage.reports.s3.endpoint", "http://localhost:8020")
        CONFIG.set("storage.reports.s3.access_key", "accessKey1")
        CONFIG.set("storage.reports.s3.secret_key", "secretKey1")
        CONFIG.set("storage.reports.s3.bucket_name", self.reports_s3_bucket_name)
        self.reports_s3_backend = S3Backend(FileUsage.REPORTS)
        self.reports_s3_backend.client.create_bucket(
            Bucket=self.reports_s3_bucket_name, ACL="private"
        )

    def tearDown(self):
        def delete_objects_in_bucket(client, bucket_name):
            paginator = client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name)
            for page in pages:
                if "Contents" not in page:
                    continue
                for obj in page["Contents"]:
                    client.delete_object(Bucket=bucket_name, Key=obj["Key"])

        delete_objects_in_bucket(self.media_s3_backend.client, self.media_s3_bucket_name)
        self.media_s3_backend.client.delete_bucket(Bucket=self.media_s3_bucket_name)
        if self.original_media_backend is not UNSET:
            CONFIG.set("storage.media.backend", self.original_media_backend)
        else:
            CONFIG.delete("storage.media.backend")
        for k, v in self.original_media_s3_settings.items():
            if v is not UNSET:
                CONFIG.set(f"storage.media.s3.{k}", v)
            else:
                CONFIG.delete(f"storage.media.s3.{k}")

        delete_objects_in_bucket(self.reports_s3_backend.client, self.reports_s3_bucket_name)
        self.reports_s3_backend.client.delete_bucket(Bucket=self.reports_s3_bucket_name)
        if self.original_reports_backend is not UNSET:
            CONFIG.set("storage.reports.backend", self.original_reports_backend)
        else:
            CONFIG.delete("storage.reports.backend")
        for k, v in self.original_reports_s3_settings.items():
            if v is not UNSET:
                CONFIG.set(f"storage.reports.s3.{k}", v)
            else:
                CONFIG.delete(f"storage.reports.s3.{k}")
