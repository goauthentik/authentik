"""Small helper functions"""
import uuid

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.template.context import Context


def render_xml(request: HttpRequest, template: str, ctx: Context) -> HttpResponse:
    """Render template with content_type application/xml"""
    return render(request, template, context=ctx, content_type="application/xml")


def get_random_id() -> str:
    """Random hex id"""
    # It is very important that these random IDs NOT start with a number.
    random_id = "_" + uuid.uuid4().hex
    return random_id
