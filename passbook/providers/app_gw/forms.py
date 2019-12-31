"""passbook Application Security Gateway Forms"""
from django import forms
from oauth2_provider.generators import generate_client_id, generate_client_secret
from oidc_provider.models import Client

from passbook.providers.app_gw.models import ApplicationGatewayProvider


class ApplicationGatewayProviderForm(forms.ModelForm):
    """Security Gateway Provider form"""

    def save(self, *args, **kwargs):
        if not self.instance.pk:
            # New instance, so we create a new OIDC client with random keys
            self.instance.client = Client.objects.create(
                client_id=generate_client_id(), client_secret=generate_client_secret()
            )
        self.instance.client.name = self.instance.name
        self.instance.client.redirect_uris = [
            f"http://{self.instance.host}/oauth2/callback",
            f"https://{self.instance.host}/oauth2/callback",
        ]
        self.instance.client.scope = ["openid", "email"]
        self.instance.client.save()
        return super().save(*args, **kwargs)

    class Meta:

        model = ApplicationGatewayProvider
        fields = ["name", "host"]
        widgets = {
            "name": forms.TextInput(),
            "host": forms.TextInput(),
        }
