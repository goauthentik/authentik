"""passbook admin templatetags"""
import inspect
from logging import getLogger

from django import template
from django.db.models import Model

register = template.Library()
LOGGER = getLogger(__name__)

@register.simple_tag()
def get_links(model_instance):
    """Find all link_ methods on an object instance, run them and return as dict"""
    prefix = 'link_'
    links = {}

    if not isinstance(model_instance, Model):
        LOGGER.warning("Model %s is not instance of Model", model_instance)
        return links

    try:
        for name, method in inspect.getmembers(model_instance, predicate=inspect.ismethod):
            if name.startswith(prefix):
                human_name = name.replace(prefix, '').replace('_', ' ').capitalize()
                link = method()
                if link:
                    links[human_name] = link
    except NotImplementedError:
        pass

    return links
