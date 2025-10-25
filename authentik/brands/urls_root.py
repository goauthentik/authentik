"""authentik brand root URLs"""

from django.urls import path

from authentik.brands.views.webfinger import WebFingerView

urlpatterns = [
    path(".well-known/webfinger", WebFingerView.as_view(), name="webfinger"),
]
