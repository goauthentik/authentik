import shutil
from tempfile import mkdtemp

from authentik.admin.files.backends.s3 import S3Backend
from authentik.admin.files.usage import FileUsage
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id

S3_CONFIG_KEYS = {
    "endpoint",
    "access_key",
    "secret_key",
    "bucket_name",
}


class FileTestFileBackendMixin:
    def setUp(self):
        self.original_media_backend = CONFIG.get("storage.media.backend")
        self.original_media_backend_path = CONFIG.get("storage.media.file.path")
        self.media_backend_path = mkdtemp()
        CONFIG.set("storage.media.backend", "file")
        CONFIG.set("storage.media.file.path", str(self.media_backend_path))

        self.original_reports_backend = CONFIG.get("storage.reports.backend")
        self.original_reports_backend_path = CONFIG.get("storage.reports.file.path")
        self.reports_backend_path = mkdtemp()
        CONFIG.set("storage.reports.backend", "file")
        CONFIG.set("storage.reports.file.path", str(self.reports_backend_path))

    def tearDown(self):
        CONFIG.set("storage.media.backend", self.original_media_backend)
        CONFIG.set("storage.media.file.path", self.original_media_backend_path)
        shutil.rmtree(self.media_backend_path)

        CONFIG.set("storage.reports.backend", self.original_reports_backend)
        CONFIG.set("storage.reports.file.path", self.original_reports_backend_path)
        shutil.rmtree(self.reports_backend_path)


class FileTestS3BackendMixin:
    def setUp(self):
        self.original_media_backend = CONFIG.get("storage.media.backend")
        CONFIG.set("storage.media.backend", "s3")
        self.original_media_s3_settings = {}
        for key in S3_CONFIG_KEYS:
            self.original_media_s3_settings[key] = CONFIG.get(f"storage.media.s3.{key}")
        self.media_s3_bucket_name = f"authentik-test-{generate_id(10)}".lower()
        CONFIG.set("storage.media.s3.endpoint", "http://localhost:8020")
        CONFIG.set("storage.media.s3.access_key", "accessKey1")
        CONFIG.set("storage.media.s3.secret_key", "secretKey1")
        CONFIG.set("storage.media.s3.bucket_name", self.media_s3_bucket_name)
        self.media_s3_backend = S3Backend(FileUsage.MEDIA)
        self.media_s3_backend.client.create_bucket(Bucket=self.media_s3_bucket_name, ACL="private")

        self.original_reports_backend = CONFIG.get("storage.reports.backend")
        CONFIG.set("storage.reports.backend", "s3")
        self.original_reports_s3_settings = {}
        for key in S3_CONFIG_KEYS:
            self.original_reports_s3_settings[key] = CONFIG.get(f"storage.reports.s3.{key}")
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
        CONFIG.set("storage.media.backend", self.original_media_backend)
        for k, v in self.original_media_s3_settings.items():
            CONFIG.set(f"storage.media.s3.{k}", v)

        delete_objects_in_bucket(self.reports_s3_backend.client, self.reports_s3_bucket_name)
        self.reports_s3_backend.client.delete_bucket(Bucket=self.reports_s3_bucket_name)
        CONFIG.set("storage.reports.backend", self.original_reports_backend)
        for k, v in self.original_reports_s3_settings.items():
            CONFIG.set(f"storage.reports.s3.{k}", v)
