"""test file api"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from botocore.exceptions import BotoCoreError, ClientError
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from authentik.admin.files.api import FileViewSet
from authentik.admin.files.usage import Usage
from authentik.core.models import Group, User
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id


class TestFileAPI(TestCase):
    """test file api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_creates_event(self, mock_factory, mock_validate_size, mock_validate_type):
        """Test that uploading a file creates a FILE_UPLOADED event"""
        file_content = b"test file content"
        file_name = "test-upload.png"

        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        # Mock the backend to avoid actual file system operations
        backend_instance = MagicMock()
        backend_instance.file_exists.return_value = False
        backend_instance.save_file = MagicMock()
        backend_instance.file_url = MagicMock(return_value=f"/media/public/{file_name}")
        backend_instance.file_size = MagicMock(return_value=len(file_content))
        backend_instance.usage = Usage.MEDIA
        backend_instance.__class__.__name__ = "FileBackend"
        mock_factory.return_value = backend_instance

        # Upload file
        response = self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": file_name,
                "usage": Usage.MEDIA.value,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        # Verify event was created
        event = Event.objects.filter(
            action=EventAction.FILE_UPLOADED,
            context__file_path=file_name,
        ).first()

        self.assertIsNotNone(event)
        self.assertEqual(event.context["file_path"], file_name)
        self.assertEqual(event.context["usage"], Usage.MEDIA.value)
        self.assertEqual(event.context["backend"], "FileBackend")
        self.assertEqual(event.context["size"], len(file_content))
        self.assertEqual(event.context["mime_type"], "image/png")

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_delete_creates_event(self, mock_factory):
        """Test that deleting a file creates a FILE_DELETED event"""
        file_name = "test-delete.png"

        # Mock the backend to avoid actual file system operations
        backend_instance = MagicMock()
        backend_instance.delete_file = MagicMock()
        backend_instance.usage = Usage.MEDIA
        backend_instance.__class__.__name__ = "FileBackend"
        mock_factory.return_value = backend_instance

        # Delete file
        url = reverse("authentik_api:files-delete")
        response = self.client.delete(f"{url}?name={file_name}&usage={Usage.MEDIA.value}")

        self.assertEqual(response.status_code, 200)

        # Verify event was created
        event = Event.objects.filter(
            action=EventAction.FILE_DELETED,
            context__file_path=file_name,
        ).first()

        self.assertIsNotNone(event)
        self.assertEqual(event.context["file_path"], file_name)
        self.assertEqual(event.context["usage"], Usage.MEDIA.value)
        self.assertEqual(event.context["backend"], "FileBackend")

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_with_s3_backend(self, mock_factory, mock_validate_size, mock_validate_type):
        """Test that uploading to S3 backend is captured in event"""
        file_content = b"test s3 content"
        file_name = "test-s3.png"

        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        # Mock S3 backend
        backend_instance = MagicMock()
        backend_instance.file_exists.return_value = False
        backend_instance.save_file = MagicMock()
        backend_instance.file_url = MagicMock(return_value="https://s3.example.com/test-s3.png")
        backend_instance.file_size = MagicMock(return_value=len(file_content))
        backend_instance.usage = Usage.MEDIA
        backend_instance.__class__.__name__ = "S3Backend"
        mock_factory.return_value = backend_instance

        # Upload file
        response = self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": file_name,
                "usage": Usage.MEDIA.value,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        # Verify event captures S3 backend
        event = Event.objects.filter(
            action=EventAction.FILE_UPLOADED,
            context__file_path=file_name,
        ).first()

        self.assertIsNotNone(event)
        self.assertEqual(event.context["backend"], "S3Backend")
        self.assertEqual(event.context["mime_type"], "image/png")

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_delete_with_s3_backend(self, mock_factory):
        """Test that deleting from S3 backend is captured in event"""
        file_name = "test-s3-delete.png"

        # Mock S3 backend
        backend_instance = MagicMock()
        backend_instance.delete_file = MagicMock()
        backend_instance.usage = Usage.MEDIA
        backend_instance.__class__.__name__ = "S3Backend"
        mock_factory.return_value = backend_instance

        # Delete file
        url = reverse("authentik_api:files-delete")
        response = self.client.delete(f"{url}?name={file_name}&usage={Usage.MEDIA.value}")

        self.assertEqual(response.status_code, 200)

        # Verify event captures S3 backend
        event = Event.objects.filter(
            action=EventAction.FILE_DELETED,
            context__file_path=file_name,
        ).first()

        self.assertIsNotNone(event)
        self.assertEqual(event.context["backend"], "S3Backend")
        self.assertEqual(event.context["file_path"], file_name)

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_captures_http_context(
        self, mock_factory, mock_validate_size, mock_validate_type
    ):
        """Test that events capture HTTP request context"""
        file_content = b"test content"
        file_name = "test-context.png"

        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        # Mock the backend
        backend_instance = MagicMock()
        backend_instance.file_exists.return_value = False
        backend_instance.save_file = MagicMock()
        backend_instance.file_url = MagicMock(return_value=f"/media/public/{file_name}")
        backend_instance.file_size = MagicMock(return_value=len(file_content))
        backend_instance.usage = Usage.MEDIA
        backend_instance.__class__.__name__ = "FileBackend"
        mock_factory.return_value = backend_instance

        # Upload file
        self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": file_name,
                "usage": Usage.MEDIA.value,
            },
            format="multipart",
        )

        # Verify HTTP context is captured
        event = Event.objects.filter(
            action=EventAction.FILE_UPLOADED,
            context__file_path=file_name,
        ).first()

        self.assertIsNotNone(event)
        self.assertIn("http_request", event.context)
        self.assertEqual(event.context["http_request"]["method"], "POST")
        self.assertIn("/api/v3/files/upload/", event.context["http_request"]["path"])


class TestFileViewSetHelperMethods(TestCase):
    """Test FileViewSet helper methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)
        self.viewset = FileViewSet()

    def test_handle_storage_error_client_error_signature_mismatch(self):
        """Test _handle_storage_error with SignatureDoesNotMatch error"""
        error = ClientError(
            {
                "Error": {
                    "Code": "SignatureDoesNotMatch",
                    "Message": "The request signature we calculated does not match",
                }
            },
            "PutObject",
        )

        with self.assertRaises(ValidationError) as context:
            self.viewset._handle_storage_error(error, "upload file")

        self.assertIn("S3 authentication failed", str(context.exception))

    def test_handle_storage_error_client_error_no_such_bucket(self):
        """Test _handle_storage_error with NoSuchBucket error"""
        error = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "The specified bucket does not exist"}},
            "ListObjects",
        )

        with self.assertRaises(ValidationError) as context:
            self.viewset._handle_storage_error(error, "list files")

        self.assertIn("S3 bucket not found", str(context.exception))

    def test_handle_storage_error_client_error_access_denied(self):
        """Test _handle_storage_error with AccessDenied error"""
        error = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "GetObject"
        )

        with self.assertRaises(ValidationError) as context:
            self.viewset._handle_storage_error(error, "download file")

        self.assertIn("S3 access denied", str(context.exception))

    def test_handle_storage_error_client_error_generic(self):
        """Test _handle_storage_error with generic ClientError"""
        error = ClientError(
            {"Error": {"Code": "UnknownError", "Message": "Something went wrong"}}, "Operation"
        )

        with self.assertRaises(ValidationError) as context:
            self.viewset._handle_storage_error(error, "operation")

        self.assertIn("An error occurred during operation", str(context.exception))

    def test_handle_storage_error_botocore_error(self):
        """Test _handle_storage_error with BotoCoreError"""
        error = BotoCoreError()

        with self.assertRaises(ValidationError) as context:
            self.viewset._handle_storage_error(error, "connect")

        self.assertIn("Failed to connect to S3 storage", str(context.exception))

    def test_handle_storage_error_non_s3_error(self):
        """Test _handle_storage_error re-raises non-S3 errors"""
        error = RuntimeError("Some other error")

        with self.assertRaises(RuntimeError):
            self.viewset._handle_storage_error(error, "operation")

    def test_build_file_response_manageable_backend(self):
        """Test _build_file_response with manageable backend"""
        mock_backend = MagicMock()
        mock_backend.manageable = True
        mock_backend.file_url.return_value = "/media/public/test.png"
        mock_backend.file_size.return_value = 1024

        with patch("authentik.admin.files.api.add_schema_prefix") as mock_add_prefix:
            mock_add_prefix.return_value = "public/test.png"

            response = self.viewset._build_file_response("test.png", mock_backend, Usage.MEDIA)

            self.assertEqual(response["name"], "public/test.png")
            self.assertEqual(response["url"], "/media/public/test.png")
            self.assertEqual(response["size"], 1024)
            self.assertEqual(response["usage"], "media")
            mock_add_prefix.assert_called_once_with("test.png")

    def test_build_file_response_non_manageable_backend(self):
        """Test _build_file_response with non-manageable backend"""
        mock_backend = MagicMock()
        mock_backend.manageable = False
        mock_backend.file_url.return_value = "/static/icon.svg"
        mock_backend.file_size.return_value = 512

        response = self.viewset._build_file_response("/static/icon.svg", mock_backend, Usage.MEDIA)

        # Non-manageable backends should not add schema prefix
        self.assertEqual(response["name"], "/static/icon.svg")
        self.assertEqual(response["url"], "/static/icon.svg")
        self.assertEqual(response["size"], 512)

    def test_build_paginated_response_with_results(self):
        """Test _build_paginated_response with results"""
        results = [
            {"name": "file1.png"},
            {"name": "file2.jpg"},
            {"name": "file3.svg"},
        ]

        response = self.viewset._build_paginated_response(results)

        self.assertEqual(response["pagination"]["count"], 3)
        self.assertEqual(response["pagination"]["total_pages"], 1)
        self.assertEqual(response["pagination"]["start_index"], 1)
        self.assertEqual(response["pagination"]["end_index"], 3)
        self.assertEqual(len(response["results"]), 3)

    def test_build_paginated_response_empty(self):
        """Test _build_paginated_response with no results"""
        response = self.viewset._build_paginated_response([])

        self.assertEqual(response["pagination"]["count"], 0)
        self.assertEqual(response["pagination"]["total_pages"], 0)
        self.assertEqual(response["pagination"]["start_index"], 0)
        self.assertEqual(response["pagination"]["end_index"], 0)
        self.assertEqual(len(response["results"]), 0)


class TestFileViewSetUsages(TestCase):
    """Test FileViewSet usages endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    def test_usages_endpoint(self):
        """Test usages endpoint returns available usage types"""
        response = self.client.get(reverse("authentik_api:files-usages"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) > 0)

        # Verify structure
        for usage in response.data:
            self.assertIn("value", usage)
            self.assertIn("label", usage)


class TestFileViewSetList(TestCase):
    """Test FileViewSet list endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_list_files_basic(self, mock_factory):
        """Test listing files with default parameters"""
        mock_backend = MagicMock()
        mock_backend.manageable = True
        mock_backend.list_files.return_value = iter(["file1.png", "file2.jpg"])
        mock_backend.file_url.side_effect = lambda f: f"/media/{f}"
        mock_backend.file_size.return_value = 1024
        mock_backend.usage = Usage.MEDIA
        mock_factory.return_value = mock_backend

        with patch("authentik.admin.files.api.StaticBackend") as mock_static:
            with patch("authentik.admin.files.api.PassthroughBackend") as mock_passthrough:
                mock_static.return_value.list_files.return_value = iter([])
                mock_static.return_value.manageable = False
                mock_passthrough.return_value.list_files.return_value = iter([])
                mock_passthrough.return_value.manageable = False

                response = self.client.get(reverse("authentik_api:files-list"))

                self.assertEqual(response.status_code, 200)
                self.assertIn("results", response.data)
                self.assertIn("pagination", response.data)

    def test_list_files_invalid_usage(self):
        """Test listing files with invalid usage parameter"""
        response = self.client.get(reverse("authentik_api:files-list"), {"usage": "invalid"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid usage", str(response.data))

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_list_files_with_search(self, mock_factory):
        """Test listing files with search query"""
        mock_backend = MagicMock()
        mock_backend.manageable = True
        mock_backend.list_files.return_value = iter(["icon.png", "logo.jpg", "icon.svg"])
        mock_backend.file_url.side_effect = lambda f: f"/media/{f}"
        mock_backend.file_size.return_value = 1024
        mock_backend.usage = Usage.MEDIA
        mock_factory.return_value = mock_backend

        with patch("authentik.admin.files.api.StaticBackend") as mock_static:
            with patch("authentik.admin.files.api.PassthroughBackend") as mock_passthrough:
                mock_static.return_value.list_files.return_value = iter([])
                mock_static.return_value.manageable = False
                mock_passthrough.return_value.list_files.return_value = iter([])
                mock_passthrough.return_value.manageable = False

                response = self.client.get(reverse("authentik_api:files-list"), {"search": "icon"})

                self.assertEqual(response.status_code, 200)

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_list_files_with_omit_param(self, mock_factory):
        """Test listing files with omit parameter"""
        mock_backend = MagicMock()
        mock_backend.manageable = True
        mock_backend.list_files.return_value = iter(["file.png"])
        mock_backend.file_url.return_value = "/media/file.png"
        mock_backend.file_size.return_value = 1024
        mock_backend.usage = Usage.MEDIA
        mock_factory.return_value = mock_backend

        with patch("authentik.admin.files.api.StaticBackend") as mock_static:
            with patch("authentik.admin.files.api.PassthroughBackend") as mock_passthrough:
                response = self.client.get(
                    reverse("authentik_api:files-list"), {"omit": "static,passthrough"}
                )

                self.assertEqual(response.status_code, 200)
                # static and passthrough backends should not be instantiated
                mock_static.assert_not_called()
                mock_passthrough.assert_not_called()

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_list_files_handles_client_error(self, mock_factory):
        """Test list handles ClientError from backend"""
        mock_backend = MagicMock()
        mock_backend.list_files.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}, "ListObjects"
        )
        mock_backend.manageable = True
        mock_factory.return_value = mock_backend

        with patch("authentik.admin.files.api.StaticBackend"):
            with patch("authentik.admin.files.api.PassthroughBackend"):
                response = self.client.get(reverse("authentik_api:files-list"))

                self.assertEqual(response.status_code, 400)
                self.assertIn("S3 bucket not found", str(response.data))


class TestFileViewSetUpload(TestCase):
    """Test FileViewSet upload endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_file_with_custom_path(
        self, mock_factory, mock_validate_size, mock_validate_type
    ):
        """Test uploading file with custom path"""
        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        mock_backend = MagicMock()
        mock_backend.manageable = True
        mock_backend.file_exists.return_value = False
        mock_backend.save_file = MagicMock()
        mock_backend.file_url.return_value = "/media/custom/test.png"
        mock_backend.file_size.return_value = 100
        mock_backend.usage = Usage.MEDIA
        mock_backend.__class__.__name__ = "FileBackend"
        mock_factory.return_value = mock_backend

        file_content = b"test content"
        response = self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": "custom/test",
                "usage": Usage.MEDIA.value,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        mock_backend.save_file.assert_called_once()

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_file_duplicate(self, mock_factory, mock_validate_size, mock_validate_type):
        """Test uploading file that already exists"""
        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        mock_backend = MagicMock()
        mock_backend.file_exists.return_value = True
        mock_backend.manageable = True
        mock_factory.return_value = mock_backend

        file_content = b"test content"
        response = self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": "duplicate.png",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", str(response.data))

    @patch("authentik.admin.files.api.validate_file_type")
    @patch("authentik.admin.files.api.validate_file_size")
    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_upload_handles_client_error(
        self, mock_factory, mock_validate_size, mock_validate_type
    ):
        """Test upload handles ClientError from backend"""
        # Mock validation functions
        mock_validate_size.return_value = None
        mock_validate_type.return_value = None

        mock_backend = MagicMock()
        mock_backend.file_exists.return_value = False
        mock_backend.save_file.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
        )
        mock_backend.manageable = True
        mock_factory.return_value = mock_backend

        file_content = b"test content"
        response = self.client.post(
            reverse("authentik_api:files-upload"),
            {
                "file": BytesIO(file_content),
                "path": "test.png",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("S3 access denied", str(response.data))


class TestFileViewSetDelete(TestCase):
    """Test FileViewSet delete endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create(username=generate_id())
        self.group = Group.objects.create(name=generate_id(), is_superuser=True)
        self.group.users.add(self.user)
        self.group.save()
        self.client.force_login(self.user)

    def test_delete_without_name_parameter(self):
        """Test delete without name parameter"""
        url = reverse("authentik_api:files-delete")
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("name parameter is required", str(response.data))

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_delete_with_schema_prefix(self, mock_factory):
        """Test delete strips schema prefix from file path"""
        mock_backend = MagicMock()
        mock_backend.delete_file = MagicMock()
        mock_backend.usage = Usage.MEDIA
        mock_backend.__class__.__name__ = "FileBackend"
        mock_factory.return_value = mock_backend

        with patch("authentik.admin.files.api.strip_schema_prefix") as mock_strip:
            mock_strip.return_value = "test.png"

            url = reverse("authentik_api:files-delete")
            response = self.client.delete(f"{url}?name=public/test.png&usage=media")

            self.assertEqual(response.status_code, 200)
            mock_strip.assert_called_once_with("public/test.png")
            mock_backend.delete_file.assert_called_once_with("test.png")

    @patch("authentik.admin.files.api.BackendFactory.create")
    def test_delete_handles_botocore_error(self, mock_factory):
        """Test delete handles BotoCoreError from backend"""
        mock_backend = MagicMock()
        mock_backend.delete_file.side_effect = BotoCoreError()
        mock_backend.manageable = True
        mock_factory.return_value = mock_backend

        url = reverse("authentik_api:files-delete")
        response = self.client.delete(f"{url}?name=test.png&usage=media")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Failed to connect to S3 storage", str(response.data))


class TestFileSerializers(TestCase):
    """Test File serializers"""

    def test_file_serializer_fields(self):
        """Test FileSerializer has all required fields"""
        from authentik.admin.files.api import FileSerializer

        serializer = FileSerializer()
        fields = serializer.fields.keys()

        self.assertIn("name", fields)
        self.assertIn("url", fields)
        self.assertIn("mime_type", fields)
        self.assertIn("size", fields)
        self.assertIn("usage", fields)

    def test_file_upload_request_serializer_fields(self):
        """Test FileUploadRequestSerializer has all required fields"""
        from authentik.admin.files.api import FileUploadRequestSerializer

        serializer = FileUploadRequestSerializer()
        fields = serializer.fields.keys()

        self.assertIn("file", fields)
        self.assertIn("path", fields)
        self.assertIn("usage", fields)

    def test_usage_serializer_fields(self):
        """Test UsageSerializer has all required fields"""
        from authentik.admin.files.api import UsageSerializer

        serializer = UsageSerializer()
        fields = serializer.fields.keys()

        self.assertIn("value", fields)
        self.assertIn("label", fields)
