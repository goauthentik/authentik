"""authentik brand root URLs"""

from django.urls import path

from authentik.brands.views.change_password import ChangePasswordView
from authentik.brands.views.webfinger import WebFingerView

urlpatterns = [
    path(".well-known/change-password", ChangePasswordView.as_view(), name="change-password"),
    path(".well-known/webfinger", WebFingerView.as_view(), name="webfinger"),
]
