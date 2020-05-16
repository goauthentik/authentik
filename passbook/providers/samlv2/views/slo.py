"""Single Logout Views"""
from django.views import View


class SAMLPostBindingView(View):
    """Handle SAML POST-type Requests"""


class SAMLRedirectBindingView(View):
    """Handle SAML Redirect-type Requests"""
