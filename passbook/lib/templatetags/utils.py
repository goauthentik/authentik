"""passbook lib Templatetags"""
from hashlib import md5
from urllib.parse import urlencode

from django import template
from django.apps import apps
from django.db.models import Model
from django.template import Context
from django.utils.html import escape
from django.utils.translation import ugettext as _

from passbook.lib.config import CONFIG
from passbook.lib.utils.urls import is_url_absolute

register = template.Library()


@register.simple_tag(takes_context=True)
def back(context: Context) -> str:
    """Return a link back (either from GET paramter or referer."""
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
        return field._meta.verbose_name
    return field.__class__.__name__


@register.simple_tag(takes_context=True)
def title(context: Context, *title) -> str:
    """Return either just branding or title - branding"""
    branding = CONFIG.y("passbook.branding", "passbook")
    if not title:
        return branding
    if "request" not in context:
        return ""
    resolver_match = context.request.resolver_match
    if not resolver_match:
        return ""
    # Include App Title in title
    app = ""
    if resolver_match.namespace != "":
        dj_app = None
        namespace = context.request.resolver_match.namespace.split(":")[0]
        # New label (App URL Namespace == App Label)
        dj_app = apps.get_app_config(namespace)
        title_modifier = getattr(dj_app, "title_modifier", None)
        if title_modifier:
            app_title = dj_app.title_modifier(context.request)
            app = app_title + " -"
    return _(
        "%(title)s - %(app)s %(branding)s"
        % {
            "title": " - ".join([str(x) for x in title]),
            "branding": branding,
            "app": app,
        }
    )


@register.simple_tag
def config(path, default=""):
    """Get a setting from the database. Returns default is setting doesn't exist."""
    return CONFIG.y(path, default)


@register.filter(name="css_class")
def css_class(field, css):
    """Add css class to form field"""
    return field.as_widget(attrs={"class": css})


@register.simple_tag
def gravatar(email, size=None, rating=None):
    """
    Generates a Gravatar URL for the given email address.

    Syntax::

        {% gravatar <email> [size] [rating] %}

    Example::

        {% gravatar someone@example.com 48 pg %}
    """
    # gravatar uses md5 for their URLs, so md5 can't be avoided
    gravatar_url = "%savatar/%s" % (
        "https://secure.gravatar.com/",
        md5(email.encode("utf-8")).hexdigest(),  # nosec
    )

    parameters = [p for p in (("s", size or "158"), ("r", rating or "g"),) if p[1]]

    if parameters:
        gravatar_url += "?" + urlencode(parameters, doseq=True)

    return escape(gravatar_url)


@register.filter
def verbose_name(obj):
    """Return Object's Verbose Name"""
    if not obj:
        return ""
    return obj._meta.verbose_name


@register.filter
def form_verbose_name(obj):
    """Return ModelForm's Object's Verbose Name"""
    if not obj:
        return ""
    return obj._meta.model._meta.verbose_name
