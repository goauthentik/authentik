"""authentik admin util views"""
from typing import Any, List, Optional
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import QuerySet
from django.http import Http404
from django.http.request import HttpRequest
from django.views.generic import DeleteView, ListView, UpdateView
from django.views.generic.list import MultipleObjectMixin

from authentik.lib.utils.reflection import all_subclasses
from authentik.lib.views import CreateAssignPermView


class DeleteMessageView(SuccessMessageMixin, DeleteView):
    """DeleteView which shows `self.success_message` on successful deletion"""

    success_url = "/"

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


class SearchListMixin(MultipleObjectMixin):
    """Accept search query using `search` querystring parameter. Requires self.search_fields,
    a list of all fields to search. Can contain special lookups like __icontains"""

    search_fields: List[str]

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        if "search" in self.request.GET:
            raw_query = self.request.GET["search"]
            if raw_query == "":
                # Empty query, don't search at all
                return queryset
            search = SearchQuery(raw_query, search_type="websearch")
            return queryset.annotate(search=SearchVector(*self.search_fields)).filter(
                search=search
            )
        return queryset


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
        return model().form

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs


class InheritanceUpdateView(UpdateView):
    """UpdateView for objects using InheritanceManager"""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs

    def get_form_class(self):
        return self.get_object().form

    def get_object(self, queryset=None):
        return (
            self.model.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )


class BackSuccessUrlMixin:
    """Checks if a relative URL has been given as ?back param, and redirect to it. Otherwise
    default to self.success_url."""

    request: HttpRequest

    success_url: Optional[str]

    def get_success_url(self) -> str:
        """get_success_url from FormMixin"""
        back_param = self.request.GET.get("back")
        if back_param:
            if not bool(urlparse(back_param).netloc):
                return back_param
        return str(self.success_url)


class UserPaginateListMixin:
    """Get paginate_by value from user's attributes, defaulting to 15"""

    request: HttpRequest

    # pylint: disable=unused-argument
    def get_paginate_by(self, queryset: QuerySet) -> int:
        """get_paginate_by Function of ListView"""
        return self.request.user.attributes.get("paginate_by", 15)
