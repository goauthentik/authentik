from django.urls import path

from authentik.enterprise.providers.apple_psso.views.nonce import NonceView
from authentik.enterprise.providers.apple_psso.views.register import (
    RegisterDeviceView,
    RegisterUserView,
)
from authentik.enterprise.providers.apple_psso.views.token import TokenView

urlpatterns = [
    path("token/", TokenView.as_view(), name="token"),
    path("nonce/", NonceView.as_view(), name="nonce"),
    path("register/device/", RegisterDeviceView.as_view(), name="register-device"),
    path("register/user/", RegisterUserView.as_view(), name="register-user"),
]
