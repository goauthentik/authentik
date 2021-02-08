"""authentik admin templatetags"""
from django import template
from django.db.models import Model
from structlog.stdlib import get_logger

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
        for name in dir(model_instance):
            if not name.startswith(prefix):
                continue
            value = getattr(model_instance, name)
            if not callable(value):
                continue
            human_name = name.replace(prefix, "").replace("_", " ").capitalize()
            link = value()
            if link:
                links[human_name] = link
    except NotImplementedError:
        pass

    return links
