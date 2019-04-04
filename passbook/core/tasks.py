"""passbook core tasks"""
from datetime import datetime
from logging import getLogger

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from passbook.core.celery import CELERY_APP
from passbook.core.models import Nonce
from passbook.lib.config import CONFIG

LOGGER = getLogger(__name__)

@CELERY_APP.task()
def send_email(to_address, subject, template, context):
    """Send Email to user(s)"""
    html_content = render_to_string(template, context=context)
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject, text_content, CONFIG.y('email.from'), [to_address])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

@CELERY_APP.task()
def clean_nonces():
    """Remove expired nonces"""
    amount = Nonce.objects.filter(expires__lt=datetime.now(), expiring=True).delete()
    LOGGER.debug("Deleted expired %d nonces", amount)
