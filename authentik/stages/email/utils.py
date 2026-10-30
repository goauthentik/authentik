"""email utils"""

from email.mime.image import MIMEImage
from mimetypes import guess_extension
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail.message import sanitize_address
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation
from structlog.stdlib import get_logger

from authentik.admin.files.backends.base import get_content_type, has_theme_variable
from authentik.admin.files.backends.static import StaticBackend
from authentik.admin.files.manager import get_file_manager
from authentik.admin.files.usage import FileUsage

if TYPE_CHECKING:
    from authentik.brands.models import Brand

LOGGER = get_logger()
DEFAULT_LOGO = "/static/dist/assets/icons/icon_left_brand.png"
# Many mail clients don't render SVG, so only embed formats they all render
LOGO_CONTENT_TYPES = ["image/png", "image/jpeg", "image/gif"]


def _brand_logo(brand: Brand) -> tuple[bytes, str] | None:
    """Read the brand's logo if it can be embedded in emails"""
    name = brand.branding_logo
    content_type = get_content_type(name)
    # A themed logo has no single file to embed
    if content_type not in LOGO_CONTENT_TYPES or has_theme_variable(name):
        return None
    try:
        content = get_file_manager(FileUsage.MEDIA).read_file(name)
    except Exception as exc:  # noqa: BLE001 - a missing logo or storage outage must not stop emails
        LOGGER.warning("Failed to read brand logo, using default logo in email", logo=name, exc=exc)
        return None
    if content is None:
        return None
    return content, content_type


def logo_data(brand: Brand) -> MIMEImage:
    """Get the brand's logo as MIME Image for emails, falling back to authentik's logo"""
    logo = _brand_logo(brand)
    if logo is None:
        default_logo = DEFAULT_LOGO
        # When running tests, assets might not exist, so fallback to a different icon
        if settings.TEST:
            default_logo = "/static/authentik/sources/saml.png"
        logo = StaticBackend(FileUsage.MEDIA).read_file(default_logo), "image/png"
    content, content_type = logo
    image = MIMEImage(content, _subtype=content_type.removeprefix("image/"))
    image.add_header("Content-ID", "<logo>")
    image.add_header(
        "Content-Disposition", "inline", filename=f"logo{guess_extension(content_type)}"
    )
    return image


def _sanitize_recipients(recipients: list[tuple[str, str]]) -> list[str]:
    """Sanitize a list of (name, email) tuples into valid email addresses."""
    sanitized = []
    for recipient_name, recipient_email in recipients:
        # Remove any newline characters from name and email before sanitizing
        clean_name = recipient_name.replace("\n", " ").replace("\r", " ") if recipient_name else ""
        clean_email = recipient_email.replace("\n", "").replace("\r", "") if recipient_email else ""
        sanitized.append(sanitize_address((clean_name, clean_email), "utf-8"))
    return sanitized


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    def __init__(
        self,
        to: list[tuple[str, str]],
        cc: list[tuple[str, str]] | None = None,
        bcc: list[tuple[str, str]] | None = None,
        template_name=None,
        template_context=None,
        language="",
        **kwargs,
    ):
        sanitized_to = _sanitize_recipients(to)
        sanitized_cc = _sanitize_recipients(cc) if cc else None
        sanitized_bcc = _sanitize_recipients(bcc) if bcc else None
        super().__init__(to=sanitized_to, cc=sanitized_cc, bcc=sanitized_bcc, **kwargs)
        if not template_name:
            return
        with translation.override(language):
            html_content = render_to_string(template_name, template_context)
            try:
                text_content = render_to_string(
                    template_name.replace("html", "txt"), template_context
                )
                self.body = text_content
            except TemplateDoesNotExist:
                pass
        self.mixed_subtype = "related"
        self.attach_alternative(html_content, "text/html")
