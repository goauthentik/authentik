import json

from django.core.paginator import EmptyPage, Paginator
from django.http import HttpResponse
from django.views.generic.base import View


class SuggestionsAPIView(View):
    http_method_names = ['get']
    schema = None
    items_per_page = 100

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '')

        try:
            field_name = request.GET.get('field', '')
            field = self.get_field(field_name)
            page_number = int(request.GET.get('page', 1))
            if page_number < 1:
                raise ValueError('page must be an integer starting from 1')
            suggestions = self.get_suggestions(field=field, search=search)
        except ValueError as e:
            error = str(e) or e.__class__.__name__
            return HttpResponse(
                content=json.dumps({'error': error}, indent=2),
                content_type='application/json; charset=utf-8',
                status=400,
            )

        paginator = Paginator(suggestions, self.items_per_page)
        try:
            page = paginator.page(page_number)
        except EmptyPage:
            items = []
            has_next = False
        else:
            items = list(page.object_list)
            has_next = page.has_next()

        response = {
            'items': items,
            'page': page_number,
            'has_next': has_next,
        }
        return HttpResponse(
            content=json.dumps(response, indent=2),
            content_type='application/json; charset=utf-8',
        )

    def get_field(self, field_name):
        if not self.schema:
            raise ValueError('DjangoQL schema is undefined')
        if not field_name:
            raise ValueError('"field" parameter is required')
        parts = field_name.split('.')
        field_name = parts.pop()
        if parts:
            model_name = parts[-1]
            app_label = '.'.join(parts[:-1])
            if not app_label:
                app_label = self.schema.current_model._meta.app_label
            model_label = '.'.join([app_label, model_name])
        else:
            model_label = self.schema.model_label(self.schema.current_model)
        schema_model = self.schema.models.get(model_label)
        if not schema_model:
            raise ValueError('Unknown model: %s' % model_label)
        field_instance = schema_model.get(field_name)
        if not field_instance:
            raise ValueError('Unknown field: %s' % field_name)
        return field_instance

    def get_suggestions(self, field, search):
        if not field.suggest_options:
            raise ValueError("%s.%s doesn't support suggestions" % (
                field.model._meta.object_name,
                field.name,
            ))
        return field.get_options(search)
