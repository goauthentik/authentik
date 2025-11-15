"""Test BackendFactory implementation"""

from unittest.mock import patch

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from authentik.admin.files.backend import Usage
from authentik.admin.files.backends import FileBackend, PassthroughBackend, S3Backend, StaticBackend
from authentik.admin.files.factory import BackendFactory, _register_default_backends


class TestBackendFactory(TestCase):
    """Test BackendFactory functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.usage = Usage.MEDIA

    def test_register(self):
        """Test registering a custom backend"""
        # Create a mock backend class
        class MockBackend:
            pass

        initial_count = len(BackendFactory._backends)

        # Register the backend
        BackendFactory.register("mock", MockBackend)

        # Verify it was registered
        self.assertEqual(len(BackendFactory._backends), initial_count + 1)
        self.assertEqual(BackendFactory._backends["mock"], MockBackend)

        # Clean up
        del BackendFactory._backends["mock"]

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_file_backend(self, mock_get_config):
        """Test creating FileBackend instance"""
        mock_get_config.return_value = "file"

        backend = BackendFactory.create(self.usage)

        self.assertIsInstance(backend, FileBackend)
        self.assertEqual(backend.usage, self.usage)
        mock_get_config.assert_called_once_with("backend", "file")

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_s3_backend(self, mock_get_config):
        """Test creating S3Backend instance"""
        mock_get_config.return_value = "s3"

        backend = BackendFactory.create(self.usage)

        self.assertIsInstance(backend, S3Backend)
        self.assertEqual(backend.usage, self.usage)

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_unknown_backend(self, mock_get_config):
        """Test creating backend with unknown type raises ValidationError"""
        mock_get_config.return_value = "unknown"

        with self.assertRaises(ValidationError) as context:
            BackendFactory.create(self.usage)

        self.assertIn("Unknown storage backend", str(context.exception))
        self.assertIn("unknown", str(context.exception))

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_with_default(self, mock_get_config):
        """Test create uses default 'file' backend when not configured"""
        mock_get_config.return_value = "file"

        backend = BackendFactory.create(self.usage)

        self.assertIsInstance(backend, FileBackend)
        # Verify default parameter was passed
        mock_get_config.assert_called_once_with("backend", "file")

    def test_get_static_backend(self):
        """Test getting StaticBackend instance"""
        backend = BackendFactory.get_static_backend(self.usage)

        self.assertIsInstance(backend, StaticBackend)
        self.assertEqual(backend.usage, self.usage)

    def test_get_passthrough_backend(self):
        """Test getting PassthroughBackend instance"""
        backend = BackendFactory.get_passthrough_backend(self.usage)

        self.assertIsInstance(backend, PassthroughBackend)
        self.assertEqual(backend.usage, self.usage)

    def test_default_backends_registered(self):
        """Test that default backends are registered on module import"""
        # Verify file and s3 backends are registered
        self.assertIn("file", BackendFactory._backends)
        self.assertIn("s3", BackendFactory._backends)
        self.assertEqual(BackendFactory._backends["file"], FileBackend)
        self.assertEqual(BackendFactory._backends["s3"], S3Backend)

    def test_register_overwrites_existing(self):
        """Test that registering with same name overwrites existing backend"""

        class MockBackend1:
            pass

        class MockBackend2:
            pass

        BackendFactory.register("test-overwrite", MockBackend1)
        self.assertEqual(BackendFactory._backends["test-overwrite"], MockBackend1)

        BackendFactory.register("test-overwrite", MockBackend2)
        self.assertEqual(BackendFactory._backends["test-overwrite"], MockBackend2)

        # Clean up
        del BackendFactory._backends["test-overwrite"]

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_with_reports_usage(self, mock_get_config):
        """Test creating backend with REPORTS usage"""
        mock_get_config.return_value = "file"

        backend = BackendFactory.create(Usage.REPORTS)

        self.assertIsInstance(backend, FileBackend)
        self.assertEqual(backend.usage, Usage.REPORTS)

    def test_register_default_backends_function(self):
        """Test _register_default_backends function"""
        # Clear backends
        original_backends = BackendFactory._backends.copy()
        BackendFactory._backends.clear()

        # Call registration function
        _register_default_backends()

        # Verify backends were registered
        self.assertIn("file", BackendFactory._backends)
        self.assertIn("s3", BackendFactory._backends)

        # Restore original state
        BackendFactory._backends = original_backends

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_logs_backend_info(self, mock_get_config):
        """Test that create logs backend information"""
        mock_get_config.return_value = "file"

        with self.assertLogs("authentik.admin.files.factory", level="INFO") as logs:
            backend = BackendFactory.create(self.usage)

            # Verify logging occurred
            log_output = "".join(logs.output)
            self.assertIn("Creating storage backend", log_output)
            self.assertIn("FileBackend", log_output)

    @patch("authentik.admin.files.factory.get_storage_config")
    def test_create_unknown_logs_error(self, mock_get_config):
        """Test that unknown backend logs error"""
        mock_get_config.return_value = "nonexistent"

        with self.assertLogs("authentik.admin.files.factory", level="ERROR") as logs:
            with self.assertRaises(ValidationError):
                BackendFactory.create(self.usage)

            log_output = "".join(logs.output)
            self.assertIn("Unknown storage backend configured", log_output)
            self.assertIn("nonexistent", log_output)

    def test_register_logs_debug(self):
        """Test that register logs debug information"""

        class TestBackend:
            pass

        with self.assertLogs("authentik.admin.files.factory", level="DEBUG") as logs:
            BackendFactory.register("test-debug", TestBackend)

            log_output = "".join(logs.output)
            self.assertIn("Registered backend", log_output)
            self.assertIn("test-debug", log_output)

        # Clean up
        del BackendFactory._backends["test-debug"]
