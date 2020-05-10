"""email utils"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    # pylint: disable=too-many-arguments
    def __init__(self, template_name=None, template_context=None, **kwargs):
        html_content = render_to_string(template_name, template_context)
        if "body" not in kwargs:
            kwargs["body"] = strip_tags(html_content)
        super().__init__(**kwargs)
        self.content_subtype = "html"
        self.attach_alternative(html_content, "text/html")
