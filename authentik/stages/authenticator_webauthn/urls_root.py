"""authentik webauthn root URLs"""

from django.urls import path

from authentik.stages.authenticator_webauthn.views import WebAuthnRelatedOriginsView

urlpatterns = [
    path(
        ".well-known/webauthn",
        WebAuthnRelatedOriginsView.as_view(),
        name="webauthn-related-origins",
    ),
]
