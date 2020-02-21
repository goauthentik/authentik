"""passbook admin templatetags"""
import inspect

from django import template
from django.db.models import Model
from django.utils.html import mark_safe
from structlog import get_logger

register = template.Library()
LOGGER = get_logger()


@register.simple_tag()
def get_links(model_instance):
    """Find all link_ methods on an object instance, run them and return as dict"""
    prefix = "link_"
    links = {}

    if not isinstance(model_instance, Model):
        LOGGER.warning("Model is not instance of Model", model_instance=model_instance)
        return links

    try:
        for name, method in inspect.getmembers(
            model_instance, predicate=inspect.ismethod
        ):
            if name.startswith(prefix):
                human_name = name.replace(prefix, "").replace("_", " ").capitalize()
                link = method()
                if link:
                    links[human_name] = link
    except NotImplementedError:
        pass

    return links


@register.simple_tag(takes_context=True)
def get_htmls(context, model_instance):
    """Find all html_ methods on an object instance, run them and return as dict"""
    prefix = "html_"
    htmls = []

    if not isinstance(model_instance, Model):
        LOGGER.warning("Model is not instance of Model", model_instance=model_instance)
        return htmls

    try:
        for name, method in inspect.getmembers(
            model_instance, predicate=inspect.ismethod
        ):
            if name.startswith(prefix):
                html = method(context.get("request"))
                if html:
                    htmls.append(mark_safe(html))
    except NotImplementedError:
        pass

    return htmls
