from django.views.generic.base import TemplateView


class ShellView(TemplateView):

    template_name = "administration/shell.html"
