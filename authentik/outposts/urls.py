"""authentik outposts urls"""
from django.urls import path

from authentik.outposts.views import KubernetesManifestView, SetupView

urlpatterns = [
    path(
        "<uuid:outpost_pk>/k8s/", KubernetesManifestView.as_view(), name="k8s-manifest"
    ),
    path("<uuid:outpost_pk>/", SetupView.as_view(), name="setup"),
]
