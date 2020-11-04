"""Outpost forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from passbook.admin.fields import CodeMirrorWidget, YAMLField
from passbook.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
)
from passbook.providers.proxy.models import ProxyProvider


class OutpostForm(forms.ModelForm):
    """Outpost Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["providers"].queryset = ProxyProvider.objects.all()

    class Meta:

        model = Outpost
        fields = [
            "name",
            "type",
            "service_connection",
            "providers",
            "_config",
        ]
        widgets = {
            "name": forms.TextInput(),
            "_config": CodeMirrorWidget,
        }
        field_classes = {
            "_config": YAMLField,
        }
        labels = {"_config": _("Configuration")}


class DockerServiceConnectionForm(forms.ModelForm):
    """Docker service-connection form"""

    class Meta:

        model = DockerServiceConnection
        fields = ["name", "local", "url", "tls"]
        widgets = {
            "name": forms.TextInput,
        }


class KubernetesServiceConnectionForm(forms.ModelForm):
    """Kubernetes service-connection form"""

    class Meta:

        model = KubernetesServiceConnection
        fields = [
            "name",
            "local",
            "kubeconfig",
        ]
        widgets = {
            "name": forms.TextInput,
            "kubeconfig": CodeMirrorWidget,
        }
        field_classes = {
            "kubeconfig": YAMLField,
        }
