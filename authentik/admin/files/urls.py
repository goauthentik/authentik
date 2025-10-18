"""API URLs"""

from authentik.admin.files.api import FileViewSet

api_urlpatterns = [
    ("files", FileViewSet, "files"),
]
