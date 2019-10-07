"""passbook Policy administration"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import (CreateView, DeleteView, FormView, ListView,
                                  UpdateView)
from django.views.generic.detail import DetailView

from passbook.admin.forms.policies import PolicyTestForm
from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Policy
from passbook.lib.utils.reflection import path_to_class
from passbook.policies.engine import PolicyEngine


class PolicyListView(AdminRequiredMixin, ListView):
    """Show list of all policies"""

    model = Policy
    template_name = 'administration/policy/list.html'

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in Policy.__subclasses__()}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().order_by('order').select_subclasses()


class PolicyCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Policy"""

    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:policies')
    success_message = _('Successfully created Policy')

    def get_form_class(self):
        policy_type = self.request.GET.get('type')
        model = next(x for x in Policy.__subclasses__()
                     if x.__name__ == policy_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class PolicyUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update policy"""

    model = Policy
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:policies')
    success_message = _('Successfully updated Policy')

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return Policy.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()


class PolicyDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete policy"""

    model = Policy
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:policies')
    success_message = _('Successfully deleted Policy')

    def get_object(self, queryset=None):
        return Policy.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class PolicyTestView(AdminRequiredMixin, DetailView, FormView):
    """View to test policy(s)"""

    model = Policy
    form_class = PolicyTestForm
    template_name = 'administration/policy/test.html'
    object = None

    def get_object(self, queryset=None):
        return Policy.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()

    def get_context_data(self, **kwargs):
        kwargs['policy'] = self.get_object()
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        return super().post(*args, **kwargs)

    def form_valid(self, form):
        policy = self.get_object()
        user = form.cleaned_data.get('user')
        policy_engine = PolicyEngine([policy])
        policy_engine.for_user(user).with_request(self.request).build()
        result = policy_engine.passing
        if result:
            messages.success(self.request, _('User successfully passed policy.'))
        else:
            messages.error(self.request, _("User didn't pass policy."))
        return self.render_to_response(self.get_context_data(form=form, result=result))
