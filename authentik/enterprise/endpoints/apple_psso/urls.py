from django.urls import path

from authentik.enterprise.endpoints.apple_psso.views.nonce import NonceView
from authentik.enterprise.endpoints.apple_psso.views.register import (
    RegisterDeviceView,
    RegisterUserView,
)
from authentik.enterprise.endpoints.apple_psso.views.token import TokenView

urlpatterns = [
    path("token/", TokenView.as_view(), name="token"),
    path("nonce/", NonceView.as_view(), name="nonce"),
]

api_urlpatterns = [
    path(
        "endpoints/apple_psso/register/device/",
        RegisterDeviceView.as_view(),
        name="register-device",
    ),
    path("endpoints/apple_psso/register/user/", RegisterUserView.as_view(), name="register-user"),
]
