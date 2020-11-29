"""passbook lib Templatetags"""
from hashlib import md5
from urllib.parse import urlencode

from django import template
from django.db.models import Model
from django.http.request import HttpRequest
from django.template import Context
from django.templatetags.static import static
from django.utils.html import escape, mark_safe
from structlog import get_logger

from passbook.core.models import User
from passbook.lib.config import CONFIG
from passbook.lib.utils.urls import is_url_absolute

register = template.Library()
LOGGER = get_logger()

GRAVATAR_URL = "https://secure.gravatar.com"


@register.simple_tag(takes_context=True)
def back(context: Context) -> str:
    """Return a link back (either from GET parameter or referer."""
    if "request" not in context:
        return ""
    request = context.get("request")
    url = ""
    if "HTTP_REFERER" in request.META:
        url = request.META.get("HTTP_REFERER")
    if "back" in request.GET:
        url = request.GET.get("back")

    if not is_url_absolute(url):
        return url
    return ""


@register.filter("fieldtype")
def fieldtype(field):
    """Return classname"""
    if isinstance(field.__class__, Model) or issubclass(field.__class__, Model):
        return verbose_name(field)
    return field.__class__.__name__


@register.simple_tag
def config(path, default=""):
    """Get a setting from the database. Returns default is setting doesn't exist."""
    return CONFIG.y(path, default)


@register.filter(name="css_class")
def css_class(field, css):
    """Add css class to form field"""
    return field.as_widget(attrs={"class": css})


@register.simple_tag
def avatar(user: User) -> str:
    """Get avatar, depending on passbook.avatar setting"""
    mode = CONFIG.raw.get("passbook").get("avatars")
    if mode == "none":
        return static("passbook/user-default.png")
    if mode == "gravatar":
        parameters = [
            ("s", "158"),
            ("r", "g"),
        ]
        # gravatar uses md5 for their URLs, so md5 can't be avoided
        mail_hash = md5(user.email.encode("utf-8")).hexdigest()  # nosec
        gravatar_url = (
            f"{GRAVATAR_URL}/avatar/{mail_hash}?{urlencode(parameters, doseq=True)}"
        )
        return escape(gravatar_url)
    raise ValueError(f"Invalid avatar mode {mode}")


@register.filter
def verbose_name(obj) -> str:
    """Return Object's Verbose Name"""
    if not obj:
        return ""
    if hasattr(obj, "verbose_name"):
        return obj.verbose_name
    return obj._meta.verbose_name


@register.filter
def form_verbose_name(obj) -> str:
    """Return ModelForm's Object's Verbose Name"""
    if not obj:
        return ""
    return verbose_name(obj._meta.model)


@register.filter
def doc(obj) -> str:
    """Return docstring of object"""
    return mark_safe(obj.__doc__.replace("\n", "<br>"))


@register.simple_tag(takes_context=True)
def query_transform(context: Context, **kwargs) -> str:
    """Append objects to the current querystring"""
    if "request" not in context:
        return ""
    request: HttpRequest = context["request"]
    updated = request.GET.copy()
    for key, value in kwargs.items():
        updated[key] = value
    return updated.urlencode()
