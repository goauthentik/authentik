"""passbook user view tests"""
from django.shortcuts import reverse
from django.test import TestCase

from passbook.core.forms.users import PasswordChangeForm
from passbook.core.models import User


class TestUserViews(TestCase):
    """Test User Views"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser(
            username='unittest user',
            email='unittest@example.com',
            password='test123')
        self.client.force_login(self.user)

    def test_user_settings(self):
        """Test UserSettingsView"""
        self.assertEqual(self.client.get(reverse('passbook_core:user-settings')).status_code, 200)

    def test_user_delete(self):
        """Test UserDeleteView"""
        self.assertEqual(self.client.post(reverse('passbook_core:user-delete')).status_code, 302)
        self.assertEqual(User.objects.filter(username='unittest user').exists(), False)
        self.setUp()

    def test_user_change_password(self):
        """Test UserChangePasswordView"""
        form_data = {
            'password': 'test2',
            'password_repeat': 'test2'
        }
        form = PasswordChangeForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(self.client.get(
            reverse('passbook_core:user-change-password')).status_code, 200)
        self.assertEqual(self.client.post(
            reverse('passbook_core:user-change-password'), data=form_data).status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('test2'))
