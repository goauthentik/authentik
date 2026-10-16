"""Nested user data must not load a password device for every row."""

from django.test import TestCase
from django.utils.timezone import now

from authentik.core.api.tokens import TokenViewSet
from authentik.core.api.users import UserSerializer
from authentik.core.models import Application, Token, User
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.api.tokens import (
    AccessTokenViewSet,
    AuthorizationCodeViewSet,
    RefreshTokenViewSet,
)
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.stages.consent.api import UserConsentViewSet
from authentik.stages.consent.models import UserConsent


class TestPasswordQueries(TestCase):
    """Cover both users with a password and users without a device."""

    def test_nested_password_dates(self):
        users = [create_test_user(), User.objects.create(username=generate_id())]
        provider = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        application = Application.objects.create(name=generate_id(), slug=generate_id())
        field = UserSerializer().fields["password_change_date"]
        expected = [field.to_representation(user.password_change_date) for user in users]

        for viewset in (
            TokenViewSet,
            AuthorizationCodeViewSet,
            RefreshTokenViewSet,
            AccessTokenViewSet,
            UserConsentViewSet,
        ):
            with self.subTest(viewset=viewset):
                model = viewset.queryset.model
                for user in users:
                    extra = {"code": generate_id()} if viewset is AuthorizationCodeViewSet else {}
                    if model is Token:
                        model.objects.create(user=user, identifier=generate_id())
                    elif model is UserConsent:
                        model.objects.create(user=user, application=application)
                    else:
                        model.objects.create(user=user, provider=provider, auth_time=now(), **extra)
                with self.assertNumQueries(1):
                    dates = [
                        field.to_representation(field.get_attribute(record.user))
                        for record in viewset.queryset.filter(user__in=users).order_by("user_id")
                    ]
                self.assertEqual(dates, expected)
