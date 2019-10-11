"""passbook user settings template tags"""
from typing import List

from django import template
from django.template.context import RequestContext

from passbook.core.models import Factor, Source, UserSettings
from passbook.policies.engine import PolicyEngine

register = template.Library()

@register.simple_tag(takes_context=True)
def user_factors(context: RequestContext) -> List[UserSettings]:
    """Return list of all factors which apply to user"""
    user = context.get('request').user
    _all_factors = Factor.objects.filter(enabled=True).order_by('order').select_subclasses()
    matching_factors: List[UserSettings] = []
    for factor in _all_factors:
        user_settings = factor.user_settings()
        policy_engine = PolicyEngine(factor.policies.all())
        policy_engine.for_user(user).with_request(context.get('request')).build()
        if policy_engine.passing and user_settings:
            matching_factors.append(user_settings)
    return matching_factors

@register.simple_tag(takes_context=True)
def user_sources(context: RequestContext) -> List[UserSettings]:
    """Return a list of all sources which are enabled for the user"""
    user = context.get('request').user
    _all_sources = Source.objects.filter(enabled=True).select_subclasses()
    matching_sources: List[UserSettings] = []
    for factor in _all_sources:
        user_settings = factor.user_settings()
        policy_engine = PolicyEngine(factor.policies.all())
        policy_engine.for_user(user).with_request(context.get('request')).build()
        if policy_engine.passing and user_settings:
            matching_sources.append(user_settings)
    return matching_sources
