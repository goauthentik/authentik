
"""passbook URL Configuration"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from passbook.core.views import authentication, overview

admin.autodiscover()
admin.site.login = RedirectView.as_view(pattern_name='auth-login')

urlpatterns = [
    path('auth/login/', authentication.LoginView.as_view(), name='auth-login'),
    path('', overview.OverviewView.as_view(), name='overview'),
    # Administration
    path('administration/django/', admin.site.urls),
    path('administration/', include('passbook.admin.urls')),
    path('', include('passbook.oauth_client.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
