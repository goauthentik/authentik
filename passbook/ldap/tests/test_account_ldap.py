"""passbook ldap settings"""

import os

from django.test import TestCase

from passbook.core.models import User
# from supervisr.mod.auth.ldap.forms import GeneralSettingsForm
from passbook.ldap.ldap_connector import LDAPConnector


class TestAccountLDAP(TestCase):
    """passbook ldap settings"""

    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = 'True'
        # FIXME: Loading mock settings from different config file
        # Setting.set('domain', 'mock.beryju.org')
        # Setting.set('base', 'OU=customers,DC=mock,DC=beryju,DC=org')
        # Setting.set('server', 'dc1.mock.beryju.org')
        # Setting.set('server:tls', False)
        # Setting.set('mode', GeneralSettingsForm.MODE_CREATE_USERS)
        # Setting.set('bind:user', 'CN=mockadm,OU=customers,DC=mock,DC=beryju,DC=org')
        # Setting.set('bind:password', 'b3ryju0rg!')
        self.ldap = LDAPConnector(mock=True)
        self.password = 'b3ryju0rg!'
        self.user = User.objects.create_user(
            username='test@test.test',
            email='test@test.test',
            first_name='Test user')
        self.user.save()
        self.user.is_active = False
        self.user.set_password(self.password)
        self.user.save()
        self.assertTrue(self.ldap.create_ldap_user(self.user, self.password))

    def test_change_password(self):
        """Test ldap change_password"""
        self.assertTrue(self.ldap.change_password('b4ryju1rg!', mail=self.user.email))
        self.assertTrue(self.ldap.change_password('b3ryju0rg!', mail=self.user.email))

    def test_disable_enable(self):
        """Test ldap enable and disable"""
        self.assertTrue(self.ldap.disable_user(mail=self.user.email))
        self.assertTrue(self.ldap.enable_user(mail=self.user.email))

    def test_email_used(self):
        """Test ldap is_email_used"""
        self.assertTrue(self.ldap.is_email_used(self.user.email))

    def test_auth(self):
        """Test ldap auth"""
        # self.assertTrue(self.ldap.auth_user(self.password, mail=self.user.email))
