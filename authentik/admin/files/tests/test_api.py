"""test file api"""

from io import BytesIO

from django.test import TestCase
from django.urls import reverse

from authentik.admin.files.api import get_mime_from_filename
from authentik.admin.files.manager import FileManager
from authentik.admin.files.tests.utils import FileTestFileBackendMixin
from authentik.admin.files.usage import FileUsage
from authentik.core.tests.utils import create_test_admin_user
from authentik.events.models import Event, EventAction


class TestFileAPI(FileTestFileBackendMixin, TestCase):
    """test file api"""

    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_upload_creates_event(self):
        """Test that uploading a file creates a FILE_UPLOADED event"""
        manager = FileManager(FileUsage.MEDIA)
        file_content = b"test file content"
        file_name = "test-upload.png"

        # Upload file
        response = self.client.post(
            reverse("authentik_api:files"),
            {
                "file": BytesIO(file_content),
                "name": file_name,
                "usage": FileUsage.MEDIA.value,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        # Verify event was created
        event = Event.objects.filter(action=EventAction.FILE_UPLOADED).first()

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.context["name"], file_name)
        self.assertEqual(event.context["usage"], FileUsage.MEDIA.value)
        self.assertEqual(event.context["mime_type"], "image/png")

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

        manager.delete_file(file_name)

    def test_delete_creates_event(self):
        """Test that deleting a file creates a FILE_DELETED event"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "test-delete.png"
        manager.save_file(file_name, b"test content")

        # Delete file
        response = self.client.delete(
            reverse(
                "authentik_api:files",
                query={
                    "name": file_name,
                    "usage": FileUsage.MEDIA.value,
                },
            )
        )

        self.assertEqual(response.status_code, 200)

        # Verify event was created
        event = Event.objects.filter(action=EventAction.FILE_DELETED).first()

        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.context["name"], file_name)
        self.assertEqual(event.context["usage"], FileUsage.MEDIA.value)

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

    def test_list_files_basic(self):
        """Test listing files with default parameters"""
        response = self.client.get(reverse("authentik_api:files"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {
                "name": "/static/dist/assets/images/flow_background.jpg",
                "mime_type": "image/jpeg",
            },
            response.data,
        )
        self.assertIn(
            {
                "name": "/static/authentik/sources/ldap.png",
                "mime_type": "image/png",
            },
            response.data,
        )

    def test_list_files_invalid_usage(self):
        """Test listing files with invalid usage parameter"""
        response = self.client.get(
            reverse(
                "authentik_api:files",
                query={
                    "usage": "invalid",
                },
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid usage", str(response.data))

    def test_list_files_with_search(self):
        """Test listing files with search query"""
        response = self.client.get(
            reverse(
                "authentik_api:files",
                query={
                    "search": "flow_background.jpg",
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {
                "name": "/static/dist/assets/images/flow_background.jpg",
                "mime_type": "image/jpeg",
            },
            response.data,
        )

    def test_list_files_with_manageable_only(self):
        """Test listing files with omit parameter"""
        response = self.client.get(
            reverse(
                "authentik_api:files",
                query={
                    "manageableOnly": "true",
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            {
                "name": "/static/dist/assets/images/flow_background.jpg",
                "mime_type": "image/jpeg",
            },
            response.data,
        )

    def test_upload_file_with_custom_path(self):
        """Test uploading file with custom path"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "custom/test"
        file_content = b"test content"
        response = self.client.post(
            reverse("authentik_api:files"),
            {
                "file": BytesIO(file_content),
                "name": file_name,
                "usage": FileUsage.MEDIA.value,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(manager.file_exists(file_name))
        manager.delete_file(file_name)

    def test_upload_file_duplicate(self):
        """Test uploading file that already exists"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "test-file.png"
        file_content = b"test content"
        manager.save_file(file_name, file_content)
        response = self.client.post(
            reverse("authentik_api:files"),
            {
                "file": BytesIO(file_content),
                "name": file_name,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already exists", str(response.data))
        manager.delete_file(file_name)

    def test_delete_without_name_parameter(self):
        """Test delete without name parameter"""
        response = self.client.delete(reverse("authentik_api:files"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("File name cannot be empty", str(response.data))


class TestGetMimeFromFilename(TestCase):
    """Test get_mime_from_filename function"""

    def test_image_png(self):
        """Test PNG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.png"), "image/png")

    def test_image_jpeg(self):
        """Test JPEG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.jpg"), "image/jpeg")

    def test_image_svg(self):
        """Test SVG image MIME type"""
        self.assertEqual(get_mime_from_filename("test.svg"), "image/svg+xml")

    def test_text_plain(self):
        """Test text file MIME type"""
        self.assertEqual(get_mime_from_filename("test.txt"), "text/plain")

    def test_unknown_extension(self):
        """Test unknown extension returns octet-stream"""
        self.assertEqual(get_mime_from_filename("test.unknown"), "application/octet-stream")

    def test_no_extension(self):
        """Test no extension returns octet-stream"""
        self.assertEqual(get_mime_from_filename("test"), "application/octet-stream")
