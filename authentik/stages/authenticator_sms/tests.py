"""Test SMS API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.stages.authenticator_sms.models import SMSDevice


class AuthenticatorSMSStage(APITestCase):
    """Test SMS API"""

