"""passbook URL Configuration"""
from logging import getLogger

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from passbook.core.auth import mfa
from passbook.core.views import authentication, overview, user
from passbook.lib.utils.reflection import get_apps

LOGGER = getLogger(__name__)
admin.autodiscover()
admin.site.login = RedirectView.as_view(pattern_name='passbook_core:auth-login')

core_urls = [
    # Authentication views
    path('auth/login/', authentication.LoginView.as_view(), name='auth-login'),
    path('auth/logout/', authentication.LogoutView.as_view(), name='auth-logout'),
    path('auth/sign_up/', authentication.SignUpView.as_view(), name='auth-sign-up'),
    path('auth/mfa/', mfa.MultiFactorAuthenticator.as_view(), name='mfa'),
    path('auth/mfa/denied/', mfa.MFAPermissionDeniedView.as_view(), 'mfa-denied'),
    # User views
    path('user/', user.UserSettingsView.as_view(), name='user-settings'),
    path('user/delete/', user.UserDeleteView.as_view(), name='user-delete'),
    # Overview
    path('', overview.OverviewView.as_view(), name='overview'),
]

urlpatterns = [
    # Core (include our own URLs so namespaces are used everywhere)
    path('', include((core_urls, 'passbook_core'), namespace='passbook_core')),
]

for _passbook_app in get_apps():
    if hasattr(_passbook_app, 'mountpoint'):
        _path = path(_passbook_app.mountpoint, include((_passbook_app.name+'.urls',
                                                        _passbook_app.label),
                                                       namespace=_passbook_app.label))
        urlpatterns.append(_path)
        LOGGER.debug("Loaded %s's URLs", _passbook_app.name)

urlpatterns += [
    # Administration
    path('administration/django/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
