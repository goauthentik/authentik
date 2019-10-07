"""passbook Core Authentication Test"""
import string
from random import SystemRandom

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase
from django.urls import reverse

from passbook.core.models import User
from passbook.factors.dummy.models import DummyFactor
from passbook.factors.password.models import PasswordFactor
from passbook.factors.view import AuthenticationView


class TestFactorAuthentication(TestCase):
    """passbook Core Authentication Test"""

    def setUp(self):
        super().setUp()
        self.password = ''.join(SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(8))
        self.factor, _ = PasswordFactor.objects.get_or_create(slug='password', defaults={
            'name': 'password',
            'slug': 'password',
            'order': 0,
            'backends': ['django.contrib.auth.backends.ModelBackend']
        })
        self.user = User.objects.create_user(username='test',
                                             email='test@test.test',
                                             password=self.password)

    def test_unauthenticated_raw(self):
        """test direct call to AuthenticationView"""
        response = self.client.get(reverse('passbook_core:auth-process'))
        # Response should be 302 since no pending user is set
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('passbook_core:auth-login'))

    def test_unauthenticated_prepared(self):
        """test direct call but with pending_uesr in session"""
        request = RequestFactory().get(reverse('passbook_core:auth-process'))
        request.user = AnonymousUser()
        request.session = {}
        request.session[AuthenticationView.SESSION_PENDING_USER] = self.user.pk

        response = AuthenticationView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_no_factors(self):
        """Test with all factors disabled"""
        self.factor.enabled = False
        self.factor.save()
        request = RequestFactory().get(reverse('passbook_core:auth-process'))
        request.user = AnonymousUser()
        request.session = {}
        request.session[AuthenticationView.SESSION_PENDING_USER] = self.user.pk

        response = AuthenticationView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('passbook_core:auth-denied'))
        self.factor.enabled = True
        self.factor.save()

    def test_authenticated(self):
        """Test with already logged in user"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('passbook_core:auth-process'))
        # Response should be 302 since no pending user is set
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('passbook_core:overview'))
        self.client.logout()

    def test_unauthenticated_post(self):
        """Test post request as unauthenticated user"""
        request = RequestFactory().post(reverse('passbook_core:auth-process'), data={
            'password': self.password
        })
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()  # pylint: disable=no-member
        request.session[AuthenticationView.SESSION_PENDING_USER] = self.user.pk

        response = AuthenticationView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('passbook_core:overview'))
        self.client.logout()

    def test_unauthenticated_post_invalid(self):
        """Test post request as unauthenticated user"""
        request = RequestFactory().post(reverse('passbook_core:auth-process'), data={
            'password': self.password + 'a'
        })
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()  # pylint: disable=no-member
        request.session[AuthenticationView.SESSION_PENDING_USER] = self.user.pk

        response = AuthenticationView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_multifactor(self):
        """Test view with multiple active factors"""
        DummyFactor.objects.get_or_create(name='dummy',
                                          slug='dummy',
                                          order=1)
        request = RequestFactory().post(reverse('passbook_core:auth-process'), data={
            'password': self.password
        })
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()  # pylint: disable=no-member
        request.session[AuthenticationView.SESSION_PENDING_USER] = self.user.pk

        response = AuthenticationView.as_view()(request)
        session_copy = request.session.items()
        self.assertEqual(response.status_code, 302)
        # Verify view redirects to itself after auth
        self.assertEqual(response.url, reverse('passbook_core:auth-process'))

        # Run another request with same session which should result in a logged in user
        request = RequestFactory().post(reverse('passbook_core:auth-process'))
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        for key, value in session_copy:
            request.session[key] = value
        request.session.save() # pylint: disable=no-member
        response = AuthenticationView.as_view()(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('passbook_core:overview'))
