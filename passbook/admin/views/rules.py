"""passbook Rule administration"""
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Rule
from passbook.lib.utils.reflection import path_to_class


class RuleListView(AdminRequiredMixin, ListView):
    """Show list of all rules"""

    model = Rule
    template_name = 'administration/rule/list.html'

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in Rule.__subclasses__()}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().order_by('order').select_subclasses()


class RuleCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Rule"""

    template_name = 'generic/create_inheritance.html'
    success_url = reverse_lazy('passbook_admin:rules')
    success_message = _('Successfully created Rule')

    def get_form_class(self):
        rule_type = self.request.GET.get('type')
        model = next(x for x in Rule.__subclasses__()
                     if x.__name__ == rule_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class RuleUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update rule"""

    model = Rule
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:rules')
    success_message = _('Successfully updated Rule')

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return Rule.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()


class RuleDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete rule"""

    model = Rule
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:rules')
    success_message = _('Successfully updated Rule')

    def get_object(self, queryset=None):
        return Rule.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()
