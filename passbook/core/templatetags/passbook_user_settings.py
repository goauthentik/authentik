"""passbook user settings template tags"""

from django import template
from django.template.context import RequestContext

from passbook.core.models import Factor, Source
from passbook.policies.engine import PolicyEngine

register = template.Library()

@register.simple_tag(takes_context=True)
def user_factors(context: RequestContext):
    """Return list of all factors which apply to user"""
    user = context.get('request').user
    _all_factors = Factor.objects.filter(enabled=True).order_by('order').select_subclasses()
    matching_factors = []
    for factor in _all_factors:
        _link = factor.has_user_settings()
        policy_engine = PolicyEngine(factor.policies.all())
        policy_engine.for_user(user).with_request(context.get('request')).build()
        if policy_engine.passing and _link:
            matching_factors.append(_link)
    return matching_factors

@register.simple_tag(takes_context=True)
def user_sources(context: RequestContext):
    """Return a list of all sources which are enabled for the user"""
    user = context.get('request').user
    _all_sources = Source.objects.filter(enabled=True).select_subclasses()
    matching_sources = []
    for factor in _all_sources:
        _link = factor.has_user_settings()
        policy_engine = PolicyEngine(factor.policies.all())
        policy_engine.for_user(user).with_request(context.get('request')).build()
        if policy_engine.passing and _link:
            matching_sources.append(_link)
    return matching_sources
