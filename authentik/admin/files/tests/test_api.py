"""test file api"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse

from authentik.admin.files.backend import Usage
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

    def test_upload_creates_event(self):
        """Test that uploading a file creates a FILE_UPLOADED event"""
        file_content = b"test file content"
        file_name = "test-upload.txt"

        # Mock the backend to avoid actual file system operations
        with patch("authentik.admin.files.api.FileViewSet._get_backend") as mock_backend:
            backend_instance = MagicMock()
            backend_instance.save_file = MagicMock()
            backend_instance.file_url = MagicMock(return_value=f"/media/public/{file_name}")
            backend_instance.file_size = MagicMock(return_value=len(file_content))
            backend_instance.usage = Usage.MEDIA
            backend_instance.__class__.__name__ = "FileBackend"
            mock_backend.return_value = backend_instance

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
            self.assertEqual(event.context["mime_type"], "text/plain")

            # Verify user is captured
            self.assertEqual(event.user["username"], self.user.username)
            self.assertEqual(event.user["pk"], self.user.pk)

    def test_delete_creates_event(self):
        """Test that deleting a file creates a FILE_DELETED event"""
        file_name = "test-delete.txt"

        # Mock the backend to avoid actual file system operations
        with patch("authentik.admin.files.api.FileViewSet._get_backend") as mock_backend:
            backend_instance = MagicMock()
            backend_instance.delete_file = MagicMock()
            backend_instance.usage = Usage.MEDIA
            backend_instance.__class__.__name__ = "FileBackend"
            mock_backend.return_value = backend_instance

            # Delete file
            url = reverse("authentik_api:files-delete")
            response = self.client.delete(
                f"{url}?name={file_name}&usage={Usage.MEDIA.value}"
            )

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

    def test_upload_with_s3_backend(self):
        """Test that uploading to S3 backend is captured in event"""
        file_content = b"test s3 content"
        file_name = "test-s3.png"

        # Mock S3 backend
        with patch("authentik.admin.files.api.FileViewSet._get_backend") as mock_backend:
            backend_instance = MagicMock()
            backend_instance.save_file = MagicMock()
            backend_instance.file_url = MagicMock(return_value="https://s3.example.com/test-s3.png")
            backend_instance.file_size = MagicMock(return_value=len(file_content))
            backend_instance.usage = Usage.MEDIA
            backend_instance.__class__.__name__ = "S3Backend"
            mock_backend.return_value = backend_instance

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

    def test_delete_with_s3_backend(self):
        """Test that deleting from S3 backend is captured in event"""
        file_name = "test-s3-delete.pdf"

        # Mock S3 backend
        with patch("authentik.admin.files.api.FileViewSet._get_backend") as mock_backend:
            backend_instance = MagicMock()
            backend_instance.delete_file = MagicMock()
            backend_instance.usage = Usage.MEDIA
            backend_instance.__class__.__name__ = "S3Backend"
            mock_backend.return_value = backend_instance

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

    def test_upload_captures_http_context(self):
        """Test that events capture HTTP request context"""
        file_content = b"test content"
        file_name = "test-context.txt"

        # Mock the backend
        with patch("authentik.admin.files.api.FileViewSet._get_backend") as mock_backend:
            backend_instance = MagicMock()
            backend_instance.save_file = MagicMock()
            backend_instance.file_url = MagicMock(return_value=f"/media/public/{file_name}")
            backend_instance.file_size = MagicMock(return_value=len(file_content))
            backend_instance.usage = Usage.MEDIA
            backend_instance.__class__.__name__ = "FileBackend"
            mock_backend.return_value = backend_instance

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
