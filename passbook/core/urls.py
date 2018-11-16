
"""passbook URL Configuration"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from passbook.core.views import authentication, overview

admin.autodiscover()
admin.site.login = RedirectView.as_view(pattern_name='passbook_core:auth-login')

core_urls = [
    path('auth/login/', authentication.LoginView.as_view(), name='auth-login'),
    path('', overview.OverviewView.as_view(), name='overview'),
]

urlpatterns = [
    # Core
    path('', include((core_urls, 'passbook_core'), namespace='passbook_core')),
    # Administration
    path('administration/django/', admin.site.urls),
    path('administration/',
         include(('passbook.admin.urls', 'passbook_admin'), namespace='passbook_admin')),
    path('source/oauth/', include(('passbook.oauth_client.urls',
                                   'passbook_oauth_client'), namespace='passbook_oauth_client')),
    path('application/oauth/', include(('passbook.oauth_provider.urls',
                                        'passbook_oauth_provider'),
                                       namespace='passbook_oauth_provider')),
    path('application/saml/', include(('passbook.saml_idp.urls',
                                       'passbook_saml_idp'),
                                      namespace='passbook_saml_idp')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
