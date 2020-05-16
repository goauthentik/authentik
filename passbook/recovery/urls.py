"""recovery views"""

from django.urls import path

from passbook.recovery.views import UseTokenView

urlpatterns = [
    path("use-token/<uuid:uuid>/", UseTokenView.as_view(), name="use-token"),
]
