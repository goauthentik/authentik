"""Core OAauth Views"""

from logging import getLogger

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import RedirectView, View

from passbook.core.auth.view import AuthenticationView, _redirect_with_qs
from passbook.lib.utils.reflection import app
from passbook.oauth_client.clients import get_client
from passbook.oauth_client.models import OAuthSource, UserOAuthSourceConnection

LOGGER = getLogger(__name__)


# pylint: disable=too-few-public-methods
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
        return reverse('passbook_oauth_client:oauth-client-callback',
                       kwargs={'source_slug': source.slug})

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
                LOGGER.debug("Handling new user")
                return self.handle_new_user(self.source, connection, info)
            LOGGER.debug("Handling existing user")
            return self.handle_existing_user(self.source, user, connection, info)

    # pylint: disable=unused-argument
    def get_callback_url(self, source):
        "Return callback url if different than the current url."
        return False

    # pylint: disable=unused-argument
    def get_error_redirect(self, source, reason):
        "Return url to redirect on login failure."
        return settings.LOGIN_URL

    def get_or_create_user(self, source, access, info):
        "Create a shell auth.User."
        raise NotImplementedError()

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

    def handle_login(self, user, source, access):
        """Prepare AuthenticationView, redirect users to remaining Factors"""
        user = authenticate(source=access.source,
                            identifier=access.identifier, request=self.request)
        self.request.session[AuthenticationView.SESSION_PENDING_USER] = user.pk
        self.request.session[AuthenticationView.SESSION_USER_BACKEND] = user.backend
        self.request.session[AuthenticationView.SESSION_IS_SSO_LOGIN] = True
        return _redirect_with_qs('passbook_core:auth-process', self.request.GET)

    # pylint: disable=unused-argument
    def handle_existing_user(self, source, user, access, info):
        "Login user and redirect."
        messages.success(self.request, _("Successfully authenticated with %(source)s!" % {
            'source': self.source.name
        }))
        return self.handle_login(user, source, access)

    def handle_login_failure(self, source, reason):
        "Message user and redirect on error."
        LOGGER.warning('Authentication Failure: %s', reason)
        messages.error(self.request, _('Authentication Failed.'))
        return redirect(self.get_error_redirect(source, reason))

    def handle_new_user(self, source, access, info):
        "Create a shell auth.User and redirect."
        was_authenticated = False
        if self.request.user.is_authenticated:
            # there's already a user logged in, just link them up
            user = self.request.user
            was_authenticated = True
        else:
            user = self.get_or_create_user(source, access, info)
        access.user = user
        access.save()
        UserOAuthSourceConnection.objects.filter(pk=access.pk).update(user=user)
        if app('passbook_audit'):
            pass
            # TODO: Create audit entry
            # from passbook.audit.models import something
            # something.event(user=user,)
            # Event.create(
            #     user=user,
            #     message=_("Linked user with OAuth source %s" % self.source.name),
            #     request=self.request,
            #     hidden=True,
            #     current=False)
        if was_authenticated:
            messages.success(self.request, _("Successfully linked %(source)s!" % {
                'source': self.source.name
            }))
            return redirect(reverse('passbook_oauth_client:oauth-client-user', kwargs={
                'source_slug': self.source.slug
            }))
        # User was not authenticated, new user has been created
        user = authenticate(source=access.source,
                            identifier=access.identifier, request=self.request)
        messages.success(self.request, _("Successfully authenticated with %(source)s!" % {
            'source': self.source.name
        }))
        return self.handle_login(user, source, access)


class DisconnectView(LoginRequiredMixin, View):
    """Delete connection with source"""

    source = None
    aas = None

    def dispatch(self, request, source_slug):
        self.source = get_object_or_404(OAuthSource, slug=source_slug)
        self.aas = get_object_or_404(UserOAuthSourceConnection,
                                     source=self.source, user=request.user)
        return super().dispatch(request, source_slug)

    def post(self, request, source_slug):
        """Delete connection object"""
        if 'confirmdelete' in request.POST:
            # User confirmed deletion
            self.aas.delete()
            messages.success(request, _('Connection successfully deleted'))
            return redirect(reverse('passbook_oauth_client:oauth-client-user', kwargs={
                'source_slug': self.source.slug
            }))
        return self.get(request, source_slug)

    def get(self, request, source):
        """Show delete form"""
        return render(request, 'generic/delete.html', {
            'object': self.source,
            'delete_url': reverse('passbook_oauth_client:oauth-client-disconnect', kwargs={
                'source_slug': self.source.slug,
            })
        })
