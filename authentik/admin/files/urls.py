from django.urls import path

from authentik.admin.files.api import FileUsedByView, FileView

api_urlpatterns = [
    path("admin/file/", FileView.as_view(), name="files"),
    path("admin/file/used_by/", FileUsedByView.as_view(), name="files-used-by"),
]
