"""email utils"""
from email.mime.image import MIMEImage
from functools import lru_cache

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation


@lru_cache()
def logo_data():
    """Get logo as MIME Image for emails"""
    with open("web/icons/icon_left_brand.png", "rb") as _logo_file:
        logo = MIMEImage(_logo_file.read())
    logo.add_header("Content-ID", "logo.png")
    return logo


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    def __init__(self, template_name=None, template_context=None, language="", **kwargs):
        with translation.override(language):
            html_content = render_to_string(template_name, template_context)
        super().__init__(**kwargs)
        self.content_subtype = "html"
        self.mixed_subtype = "related"
        self.attach(logo_data())
        self.attach_alternative(html_content, "text/html")
