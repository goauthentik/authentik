"""admin shell view"""
from django.views.generic.base import TemplateView


class ShellView(TemplateView):
    """admin shell view"""

    template_name = "administration/shell.html"
