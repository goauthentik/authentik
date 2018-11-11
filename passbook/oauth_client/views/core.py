"""Core Oauth Views"""

import base64
import hashlib
from logging import getLogger

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_text, smart_bytes
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView, View

from passbook.oauth_client.clients import get_client
from passbook.oauth_client.errors import (OAuthClientEmailMissingError,
                                          OAuthClientError)
from passbook.oauth_client.models import OAuthSource, UserOAuthSourceConnection

LOGGER = getLogger(__name__)


# pylint: disable=too-few-public-methods, too-many-locals
class OAuthClientMixin:
    "Mixin for getting OAuth client for a source."

    client_class = None

    def get_client(self, source):
        "Get instance of the OAuth client for this source."
        if self.client_class is not None:
            # pylint: disable=not-callable
            return self.client_class(source)
        return get_client(source)


class OAuthRedirect(OAuthClientMixin, RedirectView):
    "Redirect user to OAuth source to enable access."

    permanent = False
    params = None

    # pylint: disable=unused-argument
    def get_additional_parameters(self, source):
        "Return additional redirect parameters for this source."
        return self.params or {}

    def get_callback_url(self, source):
        "Return the callback url for this source."
        return reverse('oauth-client-callback', kwargs={'source_slug': source.slug})

    def get_redirect_url(self, **kwargs):
        "Build redirect url for a given source."
        slug = kwargs.get('source_slug', '')
        try:
            source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404("Unknown OAuth source '%s'." % slug)
        else:
            if not source.enabled:
                raise Http404('source %s is not enabled.' % slug)
            client = self.get_client(source)
            callback = self.get_callback_url(source)
            params = self.get_additional_parameters(source)
            return client.get_redirect_url(self.request, callback=callback, parameters=params)


class OAuthCallback(OAuthClientMixin, View):
    "Base OAuth callback view."

    source_id = None
    source = None

    # pylint: disable=too-many-return-statements
    def get(self, request, *args, **kwargs):
        """View Get handler"""
        slug = kwargs.get('source_slug', '')
        try:
            self.source = OAuthSource.objects.get(slug=slug)
        except OAuthSource.DoesNotExist:
            raise Http404("Unknown OAuth source '%s'." % slug)
        else:
            if not self.source.enabled:
                raise Http404('source %s is not enabled.' % slug)
            client = self.get_client(self.source)
            callback = self.get_callback_url(self.source)
            # Fetch access token
            raw_token = client.get_access_token(self.request, callback=callback)
            if raw_token is None:
                return self.handle_login_failure(self.source, "Could not retrieve token.")
            # Fetch profile info
            info = client.get_profile_info(raw_token)
            if info is None:
                return self.handle_login_failure(self.source, "Could not retrieve profile.")
            identifier = self.get_user_id(self.source, info)
            if identifier is None:
                return self.handle_login_failure(self.source, "Could not determine id.")
            # Get or create access record
            defaults = {
                'access_token': raw_token,
            }
            existing = UserOAuthSourceConnection.objects.filter(
                source=self.source, identifier=identifier)

            if existing.exists():
                connection = existing.first()
                connection.access_token = raw_token
                UserOAuthSourceConnection.objects.filter(pk=connection.pk).update(**defaults)
            else:
                connection = UserOAuthSourceConnection(
                    source=self.source,
                    identifier=identifier,
                    access_token=raw_token
                )
            user = authenticate(source=self.source, identifier=identifier, request=request)
            if user is None:
                try:
                    return self.handle_new_user(self.source, connection, info)
                except OAuthClientEmailMissingError as exc:
                    return render(request, 'common/error.html', {
                        'code': 500,
                        'exc_message': _("source %(name)s didn't provide an E-Mail address." % {
                            'name': self.source.name
                        }),
                    })
                except OAuthClientError as exc:
                    return render(request, 'common/error.html', {
                        'code': 500,
                        'exc_message': str(exc),
                    })
            return self.handle_existing_user(self.source, user, connection, info)

    # pylint: disable=unused-argument
    def get_callback_url(self, source):
        "Return callback url if different than the current url."
        return False

    # pylint: disable=unused-argument
    def get_error_redirect(self, source, reason):
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    # pylint: disable=unused-argument
    def get_login_redirect(self, source, user, access, new=False):
        "Return url to redirect authenticated users."
        return 'overview'

    # pylint: disable=unused-argument
    def get_or_create_user(self, source, access, info):
        "Create a shell auth.User."
        digest = hashlib.sha1(smart_bytes(access)).digest()
        # Base 64 encode to get below 30 characters
        # Removed padding characters
        username = force_text(base64.urlsafe_b64encode(digest)).replace('=', '')
        # pylint: disable=invalid-name
        User = get_user_model() # noqa
        kwargs = {
            User.USERNAME_FIELD: username,
            'email': '',
            'password': None
        }
        return User.objects.create_user(**kwargs)

    # pylint: disable=unused-argument
    def get_user_id(self, source, info):
        "Return unique identifier from the profile info."
        id_key = self.source_id or 'id'
        result = info
        try:
            for key in id_key.split('.'):
                result = result[key]
            return result
        except KeyError:
            return None

    # pylint: disable=unused-argument
    def handle_existing_user(self, source, user, access, info):
        "Login user and redirect."
        login(self.request, user)
        messages.success(self.request, _("Successfully authenticated with %(source)s!" % {
            'source': self.source.name
        }))
        return redirect(self.get_login_redirect(source, user, access))

    def handle_login_failure(self, source, reason):
        "Message user and redirect on error."
        LOGGER.warning('Authentication Failure: %s', reason)
        messages.error(self.request, _('Authentication Failed.'))
        return redirect(self.get_error_redirect(source, reason))

    def handle_new_user(self, source, access, info):
        "Create a shell auth.User and redirect."
        if self.request.user.is_authenticated:  # pylint: disable=no-else-return
            # there's already a user logged in, just link them up
            user = self.request.user
            access.user = user
            access.save()
            UserOAuthSourceConnection.objects.filter(pk=access.pk).update(user=user)
            # Event.create(
            #     user=user,
            #     message=_("Linked user with OAuth source %s" % self.source.name),
            #     request=self.request,
            #     hidden=True,
            #     current=False)
            messages.success(self.request, _("Successfully linked %(source)s!" % {
                'source': self.source.name
            }))
            return redirect(reverse('user_settings'))
        else:
            user = self.get_or_create_user(source, access, info)
            access.user = user
            access.save()
            UserOAuthSourceConnection.objects.filter(pk=access.pk).update(user=user)
            user = authenticate(source=access.source,
                                identifier=access.identifier, request=self.request)
            login(self.request, user)
            # Event.create(
            #     user=user,
            #     message=_("Authenticated user with OAuth source %s" % self.source.name),
            #     request=self.request,
            #     hidden=True,
            #     current=False)
            messages.success(self.request, _("Successfully authenticated with %(source)s!" % {
                'source': self.source.name
            }))
            return redirect(self.get_login_redirect(source, user, access, True))


@login_required
def disconnect(request: HttpRequest, source: str) -> HttpResponse:
    """Delete connection with source"""
    source = OAuthSource.objects.filter(name=source)
    if not source.exists():
        raise Http404
    r_source = source.first()

    aas = UserOAuthSourceConnection.objects.filter(source=r_source, user=request.user)
    if not aas.exists():
        raise Http404
    r_aas = aas.first()

    if request.method == 'POST' and 'confirmdelete' in request.POST:
        # User confirmed deletion
        r_aas.delete()
        messages.success(request, _('Connection successfully deleted'))
        return redirect(reverse('user_settings'))

    return render(request, 'generic/delete.html', {
        'object': 'OAuth Connection with %s' % r_source.name,
        'delete_url': reverse('oauth-client-disconnect', kwargs={
            'source': r_source.name,
        })
    })
