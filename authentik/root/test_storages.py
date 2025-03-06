import os
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.parse import urlsplit, parse_qsl

import pytest
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.db import connection
from storages.utils import safe_join
from structlog.testing import capture_logs

from authentik.root.storages import FileStorage, S3Storage
from authentik.lib.config import CONFIG


@pytest.fixture(autouse=True)
def set_tenant_schema():
    original_schema = getattr(connection, "schema_name", None)
    connection.schema_name = "tenant1"
    yield
    if original_schema is not None:
        connection.schema_name = original_schema


@pytest.fixture
def media_settings(tmp_path, monkeypatch):
    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setattr(settings, "MEDIA_ROOT", str(media_root))
    monkeypatch.setattr(settings, "MEDIA_URL", "http://example.com/media/")
    return media_root


class TestFileStorage:
    def test_basic_operations(self, media_settings):
        fs = FileStorage()
        test_content = b"test content"
        
        # Test save and retrieve
        fs.save("test.txt", test_content)
        assert fs.exists("test.txt")
        
        # Test path resolution
        full_path = fs.path("test.txt")
        assert str(media_settings / "tenant1" / "test.txt") in full_path
        
        # Test URL generation
        assert fs.url("test.txt") == "http://example.com/media/tenant1/test.txt"

    def test_directory_creation_failure(self, media_settings, monkeypatch):
        monkeypatch.setattr(Path, "mkdir", MagicMock(side_effect=PermissionError("Denied")))
        
        with capture_logs() as logs:
            with pytest.raises(PermissionError):
                FileStorage()
                
        assert any(log["event"] == "Permission denied creating storage directory" for log in logs)

    def test_suspicious_path(self, media_settings):
        fs = FileStorage()
        with capture_logs() as logs:
            with pytest.raises(SuspiciousOperation):
                fs.path("../illegal.txt")
                
        assert any(log["event"] == "Invalid file path requested" for log in logs)

    def test_media_url_format(self, media_settings, monkeypatch):
        monkeypatch.setattr(settings, "MEDIA_URL", "http://example.com/media")
        fs = FileStorage()
        
        with capture_logs() as logs:
            url = fs.base_url
            
        assert any(log["event"] == "MEDIA_URL should end with '/' for proper URL composition" for log in logs)
        assert url == "http://example.com/media/tenant1/"


class TestS3Storage:
    @pytest.fixture(autouse=True)
    def mock_config(self, monkeypatch):
        config_values = {
            "storage.media.s3.session_profile": None,
            "storage.media.s3.access_key": "test_key",
            "storage.media.s3.secret_key": "test_secret",
            "storage.media.s3.security_token": None,
        }
        monkeypatch.setattr(CONFIG, "refresh", lambda key, default: config_values.get(key, default))

    @pytest.fixture
    def mock_boto(self, monkeypatch):
        mock_client = MagicMock()
        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        monkeypatch.setattr(boto3, "Session", mock_session)
        return mock_session, mock_client

    def test_valid_configuration(self):
        storage = S3Storage()
        assert storage.access_key == "test_key"
        assert storage.secret_key == "test_secret"

    def test_conflicting_config(self, monkeypatch):
        monkeypatch.setattr(CONFIG, "refresh", lambda key, _: "value" if key == "storage.media.s3.session_profile" else "conflict")
        
        with capture_logs() as logs:
            with pytest.raises(ImproperlyConfigured):
                S3Storage()
                
        assert any(log["event"] == "Conflicting S3 storage configuration" for log in logs)

    def test_client_initialization(self, mock_boto):
        mock_session, mock_client = mock_boto
        storage = S3Storage()
        
        # First access creates client
        client = storage.client
        mock_session.assert_called_with(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_session_token=None,
            profile_name=None
        )
        assert client == mock_client

    def test_client_initialization_failure(self, monkeypatch):
        monkeypatch.setattr(boto3, "Session", MagicMock(side_effect=NoCredentialsError()))
        
        with capture_logs() as logs:
            with pytest.raises(ImproperlyConfigured):
                S3Storage().client
                
        assert any(log["event"] == "AWS credentials/region configuration error" for log in logs)

    def test_normalize_name(self):
        storage = S3Storage()
        normalized = storage._normalize_name("test.txt")
        assert normalized == "tenant1/test.txt"

    def test_suspicious_normalization(self):
        storage = S3Storage()
        with capture_logs() as logs:
            with pytest.raises(SuspiciousOperation):
                storage._normalize_name("../../invalid.txt")
                
        assert any(log["event"] == "Invalid S3 key path detected" for log in logs)

    @patch("uuid.uuid4")
    def test_filename_randomization(self, mock_uuid):
        mock_uuid.return_value = uuid.UUID(bytes=b"\x00"*16)
        storage = S3Storage()
        filename = storage._randomize_filename("document.pdf")
        assert filename == "00000000000000000000000000000000.pdf"

    def test_save_operation(self, mock_boto):
        mock_client = mock_boto[1]
        storage = S3Storage()
        
        with capture_logs() as logs:
            storage._save("test.txt", b"content")
            
        assert any(log["event"] == "Saving file to S3" for log in logs)
        mock_client.upload_fileobj.assert_called_once()

    def test_url_generation(self):
        storage = S3Storage()
        storage.custom_domain = "cdn.example.com"
        
        with patch.object(BaseS3Storage, "url", return_value="https://cdn.example.com/file?x-amz-signature=test"):
            url = storage.url("file")
            assert "x-amz-signature" not in url

    def test_error_handling(self, mock_boto):
        mock_client = mock_boto[1]
        mock_client.upload_fileobj.side_effect = ClientError(
            error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
            operation_name="Upload"
        )
        
        storage = S3Storage()
        with capture_logs() as logs:
            with pytest.raises(ClientError):
                storage._save("test.txt", b"content")
                
        assert any(log["event"] == "S3 upload failed" for log in logs)

    def test_filename_validation(self):
        storage = S3Storage()
        with patch.object(BaseS3Storage, "get_valid_name", return_value="clean_name"):
            valid_name = storage.get_valid_name("  messy/name.txt  ")
            assert valid_name == "clean_name"


class TestTenantAwareStorage:
    def test_tenant_prefix(self):
        class TestStorage(TenantAwareStorage):
            pass
            
        storage = TestStorage()
        assert storage.tenant_prefix == "tenant1"
        
    def test_get_tenant_path(self):
        class TestStorage(TenantAwareStorage):
            pass
            
        storage = TestStorage()
        assert storage.get_tenant_path("file.txt") == "tenant1/file.txt"
