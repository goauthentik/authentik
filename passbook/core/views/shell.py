"""core shell view"""
from django.views.generic.base import TemplateView


class ShellView(TemplateView):
    """core shell view"""

    template_name = "shell.html"
