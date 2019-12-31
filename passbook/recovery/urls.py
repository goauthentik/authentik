"""recovery views"""

from django.urls import path

from passbook.recovery.views import UseNonceView

urlpatterns = [
    path("use-nonce/<uuid:uuid>/", UseNonceView.as_view(), name="use-nonce"),
]
