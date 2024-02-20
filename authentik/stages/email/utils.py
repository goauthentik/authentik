"""email utils"""

from email.mime.image import MIMEImage
from functools import lru_cache
from pathlib import Path

from django.core.mail import EmailMultiAlternatives
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation


@lru_cache()
def logo_data() -> MIMEImage:
    """Get logo as MIME Image for emails"""
    path = Path("web/icons/icon_left_brand.png")
    if not path.exists():
        path = Path("web/dist/assets/icons/icon_left_brand.png")
    with open(path, "rb") as _logo_file:
        logo = MIMEImage(_logo_file.read())
    logo.add_header("Content-ID", "logo.png")
    return logo


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    def __init__(self, template_name=None, template_context=None, language="", **kwargs):
        super().__init__(**kwargs)
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
