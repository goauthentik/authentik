"""oidc provider URLs"""
from django.conf.urls import url

from passbook.providers.oidc.views import AuthorizationFlowInitView, ProviderInfoView

urlpatterns = [
    url(r"^authorize/?$", AuthorizationFlowInitView.as_view(), name="authorize"),
    url(
        r"^\.well-known/openid-configuration/?$",
        ProviderInfoView.as_view(),
        name="provider-info",
    ),
]
