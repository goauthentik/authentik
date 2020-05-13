"""passbook user settings template tags"""
from typing import Iterable, List

from django import template
from django.template.context import RequestContext

from passbook.core.models import Source
from passbook.core.types import UIUserSettings
from passbook.flows.models import Stage
from passbook.policies.engine import PolicyEngine

register = template.Library()


@register.simple_tag(takes_context=True)
# pylint: disable=unused-argument
def user_stages(context: RequestContext) -> List[UIUserSettings]:
    """Return list of all stages which apply to user"""
    _all_stages: Iterable[Stage] = Stage.objects.all().select_subclasses()
    matching_stages: List[UIUserSettings] = []
    for stage in _all_stages:
        user_settings = stage.ui_user_settings
        if not user_settings:
            continue
        matching_stages.append(user_settings)
    print(matching_stages)
    return matching_stages


@register.simple_tag(takes_context=True)
def user_sources(context: RequestContext) -> List[UIUserSettings]:
    """Return a list of all sources which are enabled for the user"""
    user = context.get("request").user
    _all_sources: Iterable[Source] = (
        Source.objects.filter(enabled=True).select_subclasses()
    )
    matching_sources: List[UIUserSettings] = []
    for source in _all_sources:
        user_settings = source.ui_user_settings
        if not user_settings:
            continue
        policy_engine = PolicyEngine(
            source.policies.all(), user, context.get("request")
        )
        policy_engine.build()
        if policy_engine.passing:
            matching_sources.append(user_settings)
    return matching_sources
