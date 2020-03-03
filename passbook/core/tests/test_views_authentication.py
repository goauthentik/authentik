"""passbook Core Account Test"""
import string
from random import SystemRandom

from django.test import TestCase
from django.urls import reverse

from passbook.core.forms.authentication import LoginForm, SignUpForm
from passbook.core.models import User


class TestAuthenticationViews(TestCase):
    """passbook Core Account Test"""

    def setUp(self):
        super().setUp()
        self.sign_up_data = {
            "name": "Test",
            "username": "beryjuorg",
            "email": "unittest@passbook.beryju.org",
            "password": "B3ryju0rg!",
            "password_repeat": "B3ryju0rg!",
        }
        self.login_data = {
            "uid_field": "unittest@example.com",
        }
        self.user = User.objects.create_superuser(
            username="unittest user",
            email="unittest@example.com",
            password="".join(
                SystemRandom().choice(string.ascii_uppercase + string.digits)
                for _ in range(8)
            ),
        )

    def test_sign_up_view(self):
        """Test account.sign_up view (Anonymous)"""
        self.client.logout()
        response = self.client.get(reverse("passbook_core:auth-sign-up"))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        """Test account.login view (Anonymous)"""
        self.client.logout()
        response = self.client.get(reverse("passbook_core:auth-login"))
        self.assertEqual(response.status_code, 200)
        # test login with post
        form = LoginForm(self.login_data)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("passbook_core:auth-login"), data=form.cleaned_data
        )
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """Test account.logout view"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("passbook_core:auth-logout"))
        self.assertEqual(response.status_code, 302)

    def test_sign_up_view_auth(self):
        """Test account.sign_up view (Authenticated)"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("passbook_core:auth-logout"))
        self.assertEqual(response.status_code, 302)

    def test_login_view_auth(self):
        """Test account.login view (Authenticated)"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("passbook_core:auth-login"))
        self.assertEqual(response.status_code, 302)

    def test_login_view_post(self):
        """Test account.login view POST (Anonymous)"""
        login_response = self.client.post(
            reverse("passbook_core:auth-login"), data=self.login_data
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response.url, reverse("passbook_core:flows-execute"))

    def test_sign_up_view_post(self):
        """Test account.sign_up view POST (Anonymous)"""
        form = SignUpForm(self.sign_up_data)
        self.assertTrue(form.is_valid())

        response = self.client.post(
            reverse("passbook_core:auth-sign-up"), data=form.cleaned_data
        )
        self.assertEqual(response.status_code, 302)

    # def test_reset_password_init_view(self):
    #     """Test account.reset_password_init view POST (Anonymous)"""
    #     form = SignUpForm(self.sign_up_data)
    #     self.assertTrue(form.is_valid())

    #     res = test_request(accounts.SignUpView.as_view(),
    #                        method='POST',
    #                        req_kwargs=form.cleaned_data)
    #     self.assertEqual(res.status_code, 302)

    #     res = test_request(accounts.PasswordResetInitView.as_view())
    #     self.assertEqual(res.status_code, 200)

    # def test_resend_confirmation(self):
    #     """Test AccountController.resend_confirmation"""
    #     form = SignUpForm(self.sign_up_data)
    #     self.assertTrue(form.is_valid())

    #     res = test_request(accounts.SignUpView.as_view(),
    #                        method='POST',
    #                        req_kwargs=form.cleaned_data)
    #     self.assertEqual(res.status_code, 302)
    #     user = User.objects.get(email=self.sign_up_data['email'])
    #     # Invalidate all other links for this user
    #     old_acs = AccountConfirmation.objects.filter(
    #         user=user)
    #     for old_ac in old_acs:
    #         old_ac.confirmed = True
    #         old_ac.save()
    #     # Create Account Confirmation UUID
    #     new_ac = AccountConfirmation.objects.create(user=user)
    #     self.assertFalse(new_ac.is_expired)
    #     on_user_confirm_resend.send(
    #         sender=None,
    #         user=user,
    #         request=None)

    # def test_reset_passowrd(self):
    #     """Test reset password POST"""
    #     # Signup user first
    #     sign_up_form = SignUpForm(self.sign_up_data)
    #     self.assertTrue(sign_up_form.is_valid())

    #     sign_up_res = test_request(accounts.SignUpView.as_view(),
    #                               method='POST',
    #                               req_kwargs=sign_up_form.cleaned_data)
    #     self.assertEqual(sign_up_res.status_code, 302)

    #     user = User.objects.get(email=self.sign_up_data['email'])
    #     # Invalidate all other links for this user
    #     old_acs = AccountConfirmation.objects.filter(
    #         user=user)
    #     for old_ac in old_acs:
    #         old_ac.confirmed = True
    #         old_ac.save()
    #     # Create Account Confirmation UUID
    #     new_ac = AccountConfirmation.objects.create(user=user)
    #     self.assertFalse(new_ac.is_expired)
    #     uuid = AccountConfirmation.objects.filter(user=user).first().pk
    #     reset_res = test_request(accounts.PasswordResetFinishView.as_view(),
    #                              method='POST',
    #                              user=user,
    #                              url_kwargs={'uuid': uuid},
    #                              req_kwargs=self.change_data)

    #     self.assertEqual(reset_res.status_code, 302)
    #     self.assertEqual(reset_res.url, reverse('common-index'))
