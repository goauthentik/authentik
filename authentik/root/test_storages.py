import pytest
from unittest.mock import patch, PropertyMock, MagicMock, call
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.conf import settings
from django.db import connection
from pathlib import Path
import os
import uuid
from botocore.exceptions import ClientError, NoCredentialsError
from storages.backends.s3 import S3Storage as BaseS3Storage

from authentik.root.storages import (
    FileStorage,
    S3Storage,
    TenantAwareStorage,
)
from authentik.lib.config import CONFIG


@pytest.fixture
def tmp_media_root(tmpdir, settings):
    settings.MEDIA_ROOT = tmpdir
    return tmpdir


@pytest.fixture
def mock_schema_name(mocker):
    return mocker.patch.object(
        connection,
        'schema_name',
        new_callable=PropertyMock(return_value='tenant1')
    )


class TestFileStorage:
    def test_initialization_creates_directory(self, tmp_media_root, mock_schema_name):
        storage = FileStorage()
        expected_dir = Path(tmp_media_root) / 'tenant1'
        assert expected_dir.exists()
        assert storage.location == str(expected_dir)

    def test_path_includes_tenant(self, tmp_media_root, mock_schema_name):
        storage = FileStorage()
        path = storage.path('test.txt')
        assert path == str(Path(tmp_media_root) / 'tenant1' / 'test.txt')

    def test_base_url_includes_tenant(self, mock_schema_name, settings):
        settings.MEDIA_URL = '/media/'
        storage = FileStorage()
        assert storage.base_url == '/media/tenant1/'

    def test_base_url_without_trailing_slash(self, mock_schema_name, settings, caplog):
        settings.MEDIA_URL = '/media'
        storage = FileStorage()
        assert storage.base_url == '/media/tenant1/'
        assert "MEDIA_URL should end with '/'" in caplog.text

    def test_suspicious_path_raises(self, mock_schema_name):
        storage = FileStorage()
        with pytest.raises(SuspiciousOperation):
            storage.path('../outside.txt')

    def test_permission_error_during_init(self, mocker, caplog):
        mock_mkdir = mocker.patch('pathlib.Path.mkdir')
        mock_mkdir.side_effect = PermissionError("Permission denied")
        with pytest.raises(PermissionError):
            FileStorage()
        assert "Permission denied creating storage directory" in caplog.text

    def test_directory_creation_error_logging(self, mocker, caplog):
        mock_mkdir = mocker.patch('pathlib.Path.mkdir')
        mock_mkdir.side_effect = OSError("Disk full")
        with pytest.raises(OSError):
            FileStorage()
        assert "Filesystem error creating storage directory" in caplog.text


class TestS3Storage:
    def test_config_validation_missing_credentials(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        with pytest.raises(ImproperlyConfigured) as exc:
            S3Storage()
        assert "Either AWS session profile" in str(exc.value)

    def test_config_validation_conflicting_credentials(self, mocker):
        def mock_config_refresh(key, default):
            if 'session_profile' in key:
                return 'profile'
            if 'access_key' in key:
                return 'key'
            return None
        
        mocker.patch.object(CONFIG, 'refresh', mock_config_refresh)
        with pytest.raises(ImproperlyConfigured) as exc:
            S3Storage()
        assert "Conflicting S3 storage configuration" in str(exc.value)

    def test_client_init_with_session_profile(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', side_effect=lambda k, d: (
            'test-profile' if 'session_profile' in k else None
        ))
        mock_session = mocker.patch('boto3.Session')
        storage = S3Storage()
        storage.client  # Trigger client creation
        mock_session.assert_called_once_with(
            profile_name='test-profile',
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_session_token=None
        )

    def test_client_init_with_access_keys(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', side_effect=lambda k, d: (
            'AKIAXXX' if 'access_key' in k else
            'secret' if 'secret_key' in k else None
        ))
        mock_session = mocker.patch('boto3.Session')
        storage = S3Storage()
        storage.client  # Trigger client creation
        mock_session.assert_called_once_with(
            profile_name=None,
            aws_access_key_id='AKIAXXX',
            aws_secret_access_key='secret',
            aws_session_token=None
        )

    def test_normalize_name_includes_tenant(self, mocker, mock_schema_name):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        storage = S3Storage()
        storage.location = 'base'
        assert storage._normalize_name('file.txt') == 'base/tenant1/file.txt'

    def test_url_strips_signing_params_with_custom_domain(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        mock_super_url = mocker.patch.object(
            BaseS3Storage, 'url', 
            return_value='https://cdn.example.com/path?X-Amz-Signature=abc&other=1'
        )
        storage = S3Storage()
        storage.custom_domain = 'cdn.example.com'
        url = storage.url('file.txt')
        assert url == 'https://cdn.example.com/path?other=1'

    def test_filename_randomization(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        storage = S3Storage()
        filename = storage._randomize_filename('document.pdf')
        assert filename.endswith('.pdf')
        assert len(filename) == 32 + len('.pdf')  # 32 hex chars + extension

    def test_client_error_handling(self, mocker, caplog):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        mock_client = MagicMock()
        mock_client.upload_fileobj.side_effect = ClientError(
            {'Error': {'Code': '403', 'Message': 'Forbidden'}}, 
            'PutObject'
        )
        mocker.patch('boto3.Session', return_value=MagicMock(client=MagicMock(return_value=mock_client)))
        
        storage = S3Storage()
        with pytest.raises(ClientError):
            storage._save('test.txt', None)
        
        assert "S3 upload failed" in caplog.text

    def test_get_valid_name_cleans_filename(self, mocker):
        mocker.patch.object(CONFIG, 'refresh', return_value=None)
        storage = S3Storage()
        assert storage.get_valid_name("../../file.txt") == 'file.txt'


class TestTenantAwareStorage:
    def test_tenant_prefix(self, mocker):
        mocker.patch.object(connection, 'schema_name', new='acme_tenant')
        class TestStorage(TenantAwareStorage):
            pass
        assert TestStorage().tenant_prefix == 'acme_tenant'

    def test_get_tenant_path(self):
        class TestStorage(TenantAwareStorage):
            @property
            def tenant_prefix(self):
                return 'test_tenant'
        
        storage = TestStorage()
        assert storage.get_tenant_path('file.txt') == 'test_tenant/file.txt'


def test_file_storage_random_filename(tmp_media_root, mock_schema_name):
    storage = FileStorage()
    name = storage._randomize_filename('image.jpg')
    assert name.endswith('.jpg')
    assert len(name) == 32 + len('.jpg')  # UUID hex + extension


def test_s3_storage_config_refresh(mocker):
    config_calls = []
    def mock_refresh(key, default):
        config_calls.append(key)
        return None
    
    mocker.patch.object(CONFIG, 'refresh', mock_refresh)
    S3Storage()
    expected_keys = [
        'storage.media.s3.session_profile',
        'storage.media.s3.access_key',
        'storage.media.s3.secret_key',
        'storage.media.s3.security_token'
    ]
    assert set(config_calls) == set(expected_keys)
