"""authentik URL Configuration"""
from django.urls import path

from authentik.admin.views import stages

urlpatterns = [
    # Stages
    path("stages/create/", stages.StageCreateView.as_view(), name="stage-create"),
    path(
        "stages/<uuid:pk>/update/",
        stages.StageUpdateView.as_view(),
        name="stage-update",
    ),
]
