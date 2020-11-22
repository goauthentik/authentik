"""core shell view"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView


class ShellView(LoginRequiredMixin, TemplateView):
    """core shell view"""

    template_name = "shell.html"
