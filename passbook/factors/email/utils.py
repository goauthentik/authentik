"""email utils"""
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class TemplateEmailMessage(EmailMultiAlternatives):
    """Wrapper around EmailMultiAlternatives with integrated template rendering"""

    # pylint: disable=too-many-arguments
    def __init__(self, subject='', body=None, from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, cc=None,
                 reply_to=None, template_name=None, template_context=None):
        html_content = render_to_string(template_name, template_context)
        if not body:
            body = strip_tags(html_content)
        super().__init__(
            subject=subject,
            body=body,
            from_email=from_email,
            to=to,
            bcc=bcc,
            connection=connection,
            attachments=attachments,
            headers=headers,
            cc=cc,
            reply_to=reply_to)
        self.attach_alternative(html_content, "text/html")
