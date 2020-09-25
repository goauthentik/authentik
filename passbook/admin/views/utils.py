"""passbook admin util views"""
from typing import Any, Dict

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import Http404
from django.http.request import HttpRequest
from django.views.generic import DeleteView, ListView, UpdateView

from passbook.lib.utils.reflection import all_subclasses
from passbook.lib.views import CreateAssignPermView


class DeleteMessageView(SuccessMessageMixin, DeleteView):
    """DeleteView which shows `self.success_message` on successful deletion"""

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class InheritanceListView(ListView):
    """ListView for objects using InheritanceManager"""

    def get_context_data(self, **kwargs):
        kwargs["types"] = {x.__name__: x for x in all_subclasses(self.model)}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class InheritanceCreateView(CreateAssignPermView):
    """CreateView for objects using InheritanceManager"""

    def get_form_class(self):
        provider_type = self.request.GET.get("type")
        try:
            model = next(
                x for x in all_subclasses(self.model) if x.__name__ == provider_type
            )
        except StopIteration as exc:
            raise Http404 from exc
        return model.form(model)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs


class InheritanceUpdateView(UpdateView):
    """UpdateView for objects using InheritanceManager"""

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs

    def get_form_class(self):
        return self.get_object().form()

    def get_object(self, queryset=None):
        return (
            self.model.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )


class UserPaginateListMixin:
    """Get paginate_by value from user's attributes, defaulting to 15"""

    request: HttpRequest

    def get_paginate_by(self, queryset: QuerySet) -> int:
        return self.request.user.attributes.get("paginate_by", 15)
