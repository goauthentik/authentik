"""passbook provider"""
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns

from allauth_passbook.provider import PassbookProvider

urlpatterns = default_urlpatterns(PassbookProvider)
