from django.urls import path

from authentik.admin.files.api import FileView

api_urlpatterns = [
    path("admin/file/", FileView.as_view(), name="files"),
]
