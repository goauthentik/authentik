from django.urls import path

from authentik.enterprise.providers.apple_psso.views.nonce import NonceView
from authentik.enterprise.providers.apple_psso.views.register import RegisterView

urlpatterns = [
    path("nonce/", NonceView.as_view(), name="nonce"),
    path("register/", RegisterView.as_view(), name="register"),
]
