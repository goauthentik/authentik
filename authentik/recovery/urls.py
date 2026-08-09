"""recovery views"""

from django.urls import path

from authentik.recovery.views import UseTokenView

urlpatterns = [
    path("use-token/<str:key>/", UseTokenView.as_view(), name="use-token"),
]
