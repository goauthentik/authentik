"""Forms for modals on overview page"""
from django import forms


class PolicyCacheClearForm(forms.Form):
    """Form to clear Policy cache"""

    title = "Clear Policy cache"
    body = """Are you sure you want to clear the policy cache?
    This will cause all policies to be re-evaluated on their next usage."""


class FlowCacheClearForm(forms.Form):
    """Form to clear Flow cache"""

    title = "Clear Flow cache"
    body = """Are you sure you want to clear the flow cache?
    This will cause all flows to be re-evaluated on their next usage."""
