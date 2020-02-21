"""passbook user settings template tags"""
from typing import Iterable, List

from django import template
from django.template.context import RequestContext

from passbook.core.models import Factor, Source
from passbook.core.types import UIUserSettings
from passbook.policies.engine import PolicyEngine

register = template.Library()


@register.simple_tag(takes_context=True)
def user_factors(context: RequestContext) -> List[UIUserSettings]:
    """Return list of all factors which apply to user"""
    user = context.get("request").user
    _all_factors: Iterable[Factor] = (
        Factor.objects.filter(enabled=True).order_by("order").select_subclasses()
    )
    matching_factors: List[UIUserSettings] = []
    for factor in _all_factors:
        user_settings = factor.ui_user_settings
        if not user_settings:
            continue
        policy_engine = PolicyEngine(
            factor.policies.all(), user, context.get("request")
        )
        policy_engine.build()
        if policy_engine.passing:
            matching_factors.append(user_settings)
    return matching_factors


@register.simple_tag(takes_context=True)
def user_sources(context: RequestContext) -> List[UIUserSettings]:
    """Return a list of all sources which are enabled for the user"""
    user = context.get("request").user
    _all_sources: Iterable[Source] = (
        Source.objects.filter(enabled=True).select_subclasses()
    )
    matching_sources: List[UIUserSettings] = []
    for factor in _all_sources:
        user_settings = factor.ui_user_settings
        if not user_settings:
            continue
        policy_engine = PolicyEngine(
            factor.policies.all(), user, context.get("request")
        )
        policy_engine.build()
        if policy_engine.passing:
            matching_sources.append(user_settings)
    return matching_sources
