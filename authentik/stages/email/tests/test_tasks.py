"""Test email stage tasks"""

from email.mime.base import MIMEBase
from pathlib import Path
from unittest.mock import PropertyMock, patch

from django.core import mail
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.locmem import EmailBackend
from django.test import TestCase

from authentik.admin.files.manager import get_file_manager
from authentik.admin.files.tests.utils import FileTestFileBackendMixin
from authentik.admin.files.usage import FileUsage
from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_admin_user, create_test_brand
from authentik.lib.generators import generate_id
from authentik.stages.authenticator_email.models import AuthenticatorEmailStage
from authentik.stages.email.models import EmailStage
from authentik.stages.email.tasks import get_email_body, send_mails
from authentik.stages.email.utils import TemplateEmailMessage

# Logo used in tests when the brand's logo can't be embedded, see logo_data
DEFAULT_LOGO = Path("web/authentik/sources/saml.png").read_bytes()


class TestEmailTasks(TestCase):
    """Test email stage tasks"""

    def setUp(self):
        self.user = create_test_admin_user()
        self.stage = EmailStage.objects.create(
            name="test-email",
            use_global_settings=True,
        )
        self.auth_stage = AuthenticatorEmailStage.objects.create(
            name="test-auth-email",
            use_global_settings=True,
        )

    def test_get_email_body_html(self):
        """Test get_email_body with HTML alternative"""
        message = EmailMultiAlternatives()
        message.body = "plain text"
        message.attach_alternative("<p>html content</p>", "text/html")
        self.assertEqual(get_email_body(message), "<p>html content</p>")

    def test_get_email_body_plain(self):
        """Test get_email_body with plain text only"""
        message = EmailMultiAlternatives()
        message.body = "plain text"
        self.assertEqual(get_email_body(message), "plain text")

    @patch(
        "authentik.stages.email.models.EmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_send_mails_email_stage(self):
        """Test send_mails with EmailStage"""
        message = EmailMultiAlternatives()
        send_mails(self.stage, message)
        self.assertEqual(len(mail.outbox), 1)

    @patch(
        "authentik.stages.authenticator_email.models.AuthenticatorEmailStage.backend_class",
        PropertyMock(return_value=EmailBackend),
    )
    def test_send_mails_authenticator_stage(self):
        """Test send_mails with AuthenticatorEmailStage"""
        message = EmailMultiAlternatives()
        send_mails(self.auth_stage, message)
        self.assertEqual(len(mail.outbox), 1)


@patch(
    "authentik.stages.email.models.EmailStage.backend_class",
    PropertyMock(return_value=EmailBackend),
)
class TestEmailLogo(FileTestFileBackendMixin, TestCase):
    """Test the logo embedded in emails"""

    def setUp(self):
        super().setUp()
        self.stage = EmailStage.objects.create(name=generate_id(), use_global_settings=True)
        self.files = get_file_manager(FileUsage.MEDIA)
        self.files.save_file("brand/logo.png", b"brand logo png")
        self.files.save_file("brand/logo.jpg", b"brand logo jpeg")
        self.files.save_file("brand/logo.svg", b"<svg></svg>")
        self.files.save_file("brand/logo-light.png", b"brand logo light")
        self.files.save_file("brand/logo-dark.png", b"brand logo dark")

    def send(self, brand: Brand | None = None) -> MIMEBase | None:
        """Send an email and return its logo attachment"""
        message = TemplateEmailMessage(
            to=[("", "foo@bar.baz")],
            template_name="email/setup.html",
            template_context={},
        )
        mail.outbox.clear()
        send_mails(self.stage, message, brand=brand)
        self.assertEqual(len(mail.outbox), 1)
        for attachment in mail.outbox[0].attachments:
            if isinstance(attachment, MIMEBase) and attachment["Content-ID"] == "<logo>":
                return attachment
        return None

    def test_png(self):
        """Test a PNG brand logo is embedded"""
        logo = self.send(Brand.objects.create(domain=generate_id(), branding_logo="brand/logo.png"))
        self.assertEqual(logo.get_payload(decode=True), b"brand logo png")
        self.assertEqual(logo.get_content_type(), "image/png")
        self.assertEqual(logo.get_filename(), "logo.png")

    def test_jpeg(self):
        """Test a JPEG brand logo is embedded with its content type"""
        logo = self.send(Brand.objects.create(domain=generate_id(), branding_logo="brand/logo.jpg"))
        self.assertEqual(logo.get_payload(decode=True), b"brand logo jpeg")
        self.assertEqual(logo.get_content_type(), "image/jpeg")
        self.assertEqual(logo.get_filename(), "logo.jpg")

    def test_static(self):
        """Test a built-in PNG logo is embedded"""
        logo = self.send(
            Brand.objects.create(
                domain=generate_id(), branding_logo="/static/authentik/sources/ldap.png"
            )
        )
        self.assertEqual(
            logo.get_payload(decode=True), Path("web/authentik/sources/ldap.png").read_bytes()
        )

    def test_fallback(self):
        """Test logos that can't be embedded fall back to the default logo"""
        for branding_logo in [
            # Many mail clients don't render SVG
            "brand/logo.svg",
            # A themed logo has no single file to embed
            "brand/logo-%(theme)s.png",
            # External files aren't read
            "https://cdn.example.com/logo.png",
            "brand/does-not-exist.png",
        ]:
            with self.subTest(branding_logo=branding_logo):
                logo = self.send(
                    Brand.objects.create(domain=generate_id(), branding_logo=branding_logo)
                )
                self.assertEqual(logo.get_payload(decode=True), DEFAULT_LOGO)
                self.assertEqual(logo.get_content_type(), "image/png")

    def test_storage_error(self):
        """Test the default logo is embedded when storage fails"""
        brand = Brand.objects.create(domain=generate_id(), branding_logo="brand/logo.png")
        with patch(
            "authentik.admin.files.manager.FileManager.read_file",
            side_effect=ConnectionError("storage unavailable"),
        ):
            logo = self.send(brand)
        self.assertEqual(logo.get_payload(decode=True), DEFAULT_LOGO)

    def test_default_brand(self):
        """Test the default brand's logo is embedded when no brand is given"""
        create_test_brand(branding_logo="brand/logo.png")
        self.assertEqual(self.send().get_payload(decode=True), b"brand logo png")

    def test_unknown_brand(self):
        """Test the default brand's logo is embedded when the brand doesn't exist anymore"""
        create_test_brand(branding_logo="brand/logo.png")
        brand = Brand(domain=generate_id(), branding_logo="brand/logo.jpg")
        self.assertEqual(self.send(brand).get_payload(decode=True), b"brand logo png")

    def test_no_default_brand(self):
        """Test the default logo is embedded when there is no brand"""
        Brand.objects.all().delete()
        self.assertEqual(self.send().get_payload(decode=True), DEFAULT_LOGO)

    def test_logo_unused(self):
        """Test no logo is attached when the template doesn't use it"""
        message = EmailMultiAlternatives(to=["foo@bar.baz"])
        message.attach_alternative("<p>no logo</p>", "text/html")
        send_mails(self.stage, message, brand=create_test_brand(branding_logo="brand/logo.png"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments, [])
