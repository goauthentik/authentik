"""test file api"""

from io import BytesIO

from django.test import TestCase
from django.urls import reverse

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
        event = Event.objects.filter(action=EventAction.MODEL_CREATED).first()

        self.assertIsNotNone(event)
        assert event is not None  # nosec
        self.assertEqual(event.context["model"]["name"], file_name)
        self.assertEqual(event.context["model"]["usage"], FileUsage.MEDIA.value)
        self.assertEqual(event.context["model"]["mime_type"], "image/png")

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

        manager.delete_file(file_name)

    def test_delete_creates_event(self):
        """Test that deleting a file creates an event"""
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
        event = Event.objects.filter(action=EventAction.MODEL_DELETED).first()

        self.assertIsNotNone(event)
        assert event is not None  # nosec
        self.assertEqual(event.context["model"]["name"], file_name)
        self.assertEqual(event.context["model"]["usage"], FileUsage.MEDIA.value)

        # Verify user is captured
        self.assertEqual(event.user["username"], self.user.username)
        self.assertEqual(event.user["pk"], self.user.pk)

    def test_list_files_basic(self):
        """Test listing files with default parameters"""
        response = self.client.get(reverse("authentik_api:files"))

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {
                "name": "/static/authentik/sources/ldap.png",
                "url": "/static/authentik/sources/ldap.png",
                "mime_type": "image/png",
                "themed_urls": None,
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
        self.assertIn("not a valid choice", str(response.data))

    def test_list_files_with_search(self):
        """Test listing files with search query"""
        response = self.client.get(
            reverse(
                "authentik_api:files",
                query={
                    "search": "ldap.png",
                },
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {
                "name": "/static/authentik/sources/ldap.png",
                "url": "/static/authentik/sources/ldap.png",
                "mime_type": "image/png",
                "themed_urls": None,
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
        self.assertIn("field is required", str(response.data))

    def test_list_files_includes_themed_urls_none(self):
        """Test listing files includes themed_urls as None for non-themed files"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "test-no-theme.png"
        manager.save_file(file_name, b"test content")

        response = self.client.get(
            reverse("authentik_api:files", query={"search": file_name, "manageableOnly": "true"})
        )

        self.assertEqual(response.status_code, 200)
        file_entry = next((f for f in response.data if f["name"] == file_name), None)
        self.assertIsNotNone(file_entry)
        self.assertIn("themed_urls", file_entry)
        self.assertIsNone(file_entry["themed_urls"])

        manager.delete_file(file_name)

    def test_list_files_includes_themed_urls_dict(self):
        """Test listing files includes themed_urls as dict for themed files"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "logo-%(theme)s.svg"
        manager.save_file("logo-light.svg", b"<svg>light</svg>")
        manager.save_file("logo-dark.svg", b"<svg>dark</svg>")
        manager.save_file(file_name, b"<svg>placeholder</svg>")

        response = self.client.get(
            reverse("authentik_api:files", query={"search": "%(theme)s", "manageableOnly": "true"})
        )

        self.assertEqual(response.status_code, 200)
        file_entry = next((f for f in response.data if f["name"] == file_name), None)
        self.assertIsNotNone(file_entry)
        self.assertIn("themed_urls", file_entry)
        self.assertIsInstance(file_entry["themed_urls"], dict)
        self.assertIn("light", file_entry["themed_urls"])
        self.assertIn("dark", file_entry["themed_urls"])

        manager.delete_file(file_name)
        manager.delete_file("logo-light.svg")
        manager.delete_file("logo-dark.svg")

    def test_upload_file_with_theme_variable(self):
        """Test uploading file with %(theme)s in name"""
        manager = FileManager(FileUsage.MEDIA)
        file_name = "brand-logo-%(theme)s.svg"
        file_content = b"<svg></svg>"

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
