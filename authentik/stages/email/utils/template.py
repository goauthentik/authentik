"""email utils"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    def __init__(self, template_name=None, template_context=None, language="", **kwargs):
        with translation.override(language):
            html_content = render_to_string(template_name, template_context)
        super().__init__(**kwargs)
        self.content_subtype = "html"
        self.attach_alternative(html_content, "text/html")
