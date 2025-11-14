"""Test Backend base class and utilities"""

from abc import ABC
from unittest.mock import MagicMock, patch

from django.test import TestCase

from authentik.admin.files.backend import Backend, Usage, get_allowed_api_usages


class ConcreteBackend(Backend):
    """Concrete implementation of Backend for testing"""

    allowed_usages = [Usage.MEDIA, Usage.REPORTS]
    manageable = True

    def supports_file_path(self, file_path: str) -> bool:
        return True

    def list_files(self):
        yield "test.txt"

    def save_file(self, name: str, content: bytes) -> None:
        pass

    def save_file_stream(self, name: str):
        pass

    def delete_file(self, name: str) -> None:
        pass

    def file_url(self, name: str) -> str:
        return f"/files/{name}"

    def file_size(self, name: str) -> int:
        return 0

    def file_exists(self, name: str) -> bool:
        return False


class NonManageableBackend(Backend):
    """Non-manageable backend for testing"""

    allowed_usages = [Usage.MEDIA]
    manageable = False

    def supports_file_path(self, file_path: str) -> bool:
        return True

    def list_files(self):
        yield from []

    def save_file(self, name: str, content: bytes) -> None:
        pass

    def save_file_stream(self, name: str):
        pass

    def delete_file(self, name: str) -> None:
        pass

    def file_url(self, name: str) -> str:
        return name

    def file_size(self, name: str) -> int:
        return 0

    def file_exists(self, name: str) -> bool:
        return False


class TestBackend(TestCase):
    """Test Backend base class"""

    def test_usage_enum(self):
        """Test Usage enum values"""
        self.assertEqual(Usage.MEDIA.value, "media")
        self.assertEqual(Usage.REPORTS.value, "reports")

    def test_usage_enum_string_inheritance(self):
        """Test Usage enum inherits from str"""
        self.assertIsInstance(Usage.MEDIA, str)
        self.assertEqual(Usage.MEDIA.value, "media")

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_backend_init_manageable(self, mock_get_config):
        """Test Backend initialization for manageable backend"""
        mock_get_config.return_value = "test"

        backend = ConcreteBackend(Usage.MEDIA)

        self.assertEqual(backend.usage, Usage.MEDIA)
        self.assertEqual(backend._backend_type, "test")
        mock_get_config.assert_called_once_with("backend", "file")

    def test_backend_init_non_manageable(self):
        """Test Backend initialization for non-manageable backend"""
        backend = NonManageableBackend(Usage.MEDIA)

        self.assertEqual(backend.usage, Usage.MEDIA)
        self.assertIsNone(backend._backend_type)

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_get_config(self, mock_get_config):
        """Test get_config method"""
        mock_get_config.side_effect = lambda key, default=None: {
            "backend": "file",
            "test.key": "test-value",
        }.get(key, default)

        backend = ConcreteBackend(Usage.MEDIA)
        value = backend.get_config("test.key", "default")

        self.assertEqual(value, "test-value")

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_get_config_with_default(self, mock_get_config):
        """Test get_config with default value"""
        mock_get_config.side_effect = lambda key, default=None: {
            "backend": "file",
        }.get(key, default)

        backend = ConcreteBackend(Usage.MEDIA)
        value = backend.get_config("nonexistent.key", "my-default")

        self.assertEqual(value, "my-default")

    def test_backend_is_abstract(self):
        """Test that Backend is an abstract base class"""
        self.assertTrue(issubclass(Backend, ABC))

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_backend_abstract_methods(self, mock_get_config):
        """Test that Backend has abstract methods"""
        mock_get_config.return_value = "test"

        # Verify abstract methods exist
        abstract_methods = Backend.__abstractmethods__
        expected_methods = {
            "supports_file_path",
            "list_files",
            "save_file",
            "save_file_stream",
            "delete_file",
            "file_url",
            "file_size",
            "file_exists",
        }

        self.assertEqual(abstract_methods, expected_methods)

    def test_class_attributes(self):
        """Test Backend class attributes"""
        self.assertEqual(Backend.allowed_usages, [])
        self.assertTrue(Backend.manageable)

    def test_concrete_backend_attributes(self):
        """Test concrete backend class attributes"""
        self.assertEqual(ConcreteBackend.allowed_usages, [Usage.MEDIA, Usage.REPORTS])
        self.assertTrue(ConcreteBackend.manageable)

    def test_non_manageable_backend_attributes(self):
        """Test non-manageable backend attributes"""
        self.assertEqual(NonManageableBackend.allowed_usages, [Usage.MEDIA])
        self.assertFalse(NonManageableBackend.manageable)

    def test_get_allowed_api_usages_function(self):
        """Test get_allowed_api_usages module function"""
        usages = get_allowed_api_usages()

        self.assertEqual(usages, [Usage.MEDIA])
        self.assertIsInstance(usages, list)
        self.assertEqual(len(usages), 1)

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_get_allowed_api_usages_class_method(self, mock_get_config):
        """Test Backend.get_allowed_api_usages class method"""
        mock_get_config.return_value = "test"

        # Manageable backend should return all allowed usages
        usages = ConcreteBackend.get_allowed_api_usages()
        self.assertEqual(usages, [Usage.MEDIA, Usage.REPORTS])

        # Non-manageable backend should return empty list
        usages = NonManageableBackend.get_allowed_api_usages()
        self.assertEqual(usages, [])

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_backend_with_reports_usage(self, mock_get_config):
        """Test Backend with REPORTS usage"""
        mock_get_config.return_value = "file"

        backend = ConcreteBackend(Usage.REPORTS)

        self.assertEqual(backend.usage, Usage.REPORTS)

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_init_logs_info(self, mock_get_config):
        """Test that initialization logs info for manageable backends"""
        mock_get_config.return_value = "test"

        with self.assertLogs("_pytest.compat", level="INFO") as logs:
            backend = ConcreteBackend(Usage.MEDIA)

        log_output = "".join(logs.output)
        self.assertIn("Initialized storage backend", log_output)
        self.assertIn("ConcreteBackend", log_output)
        self.assertIn("media", log_output)

    def test_init_no_logs_for_non_manageable(self):
        """Test that non-manageable backends don't log initialization"""
        # Non-manageable backends shouldn't trigger INFO logs
        with self.assertRaises(AssertionError):
            with self.assertLogs("authentik.admin.files.backend", level="INFO"):
                backend = NonManageableBackend(Usage.MEDIA)

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_backend_methods_callable(self, mock_get_config):
        """Test that all backend methods are callable"""
        mock_get_config.return_value = "test"

        backend = ConcreteBackend(Usage.MEDIA)

        # Verify all methods are callable
        self.assertTrue(callable(backend.supports_file_path))
        self.assertTrue(callable(backend.list_files))
        self.assertTrue(callable(backend.save_file))
        self.assertTrue(callable(backend.save_file_stream))
        self.assertTrue(callable(backend.delete_file))
        self.assertTrue(callable(backend.file_url))
        self.assertTrue(callable(backend.file_size))
        self.assertTrue(callable(backend.file_exists))

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_list_files_generator(self, mock_get_config):
        """Test that list_files returns a generator"""
        mock_get_config.return_value = "test"

        backend = ConcreteBackend(Usage.MEDIA)
        result = backend.list_files()

        # Verify it's a generator
        from collections.abc import Generator

        self.assertIsInstance(result, Generator)

        # Verify it yields expected values
        files = list(result)
        self.assertEqual(files, ["test.txt"])

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_concrete_backend_implementation(self, mock_get_config):
        """Test concrete backend implementation methods"""
        mock_get_config.return_value = "test"

        backend = ConcreteBackend(Usage.MEDIA)

        # Test supports_file_path
        self.assertTrue(backend.supports_file_path("any-file.txt"))

        # Test file_url
        self.assertEqual(backend.file_url("test.txt"), "/files/test.txt")

        # Test file_size
        self.assertEqual(backend.file_size("test.txt"), 0)

        # Test file_exists
        self.assertFalse(backend.file_exists("test.txt"))

    @patch("authentik.admin.files.backend.get_storage_config")
    def test_usage_type_preserved(self, mock_get_config):
        """Test that usage type is preserved through initialization"""
        mock_get_config.return_value = "test"

        for usage in Usage:
            backend = ConcreteBackend(usage)
            self.assertEqual(backend.usage, usage)
            self.assertIsInstance(backend.usage, Usage)
