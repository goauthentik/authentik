"""authentik user settings template tags"""
from typing import Iterable

from django import template
from django.template.context import RequestContext

from authentik.core.models import Source
from authentik.flows.models import Stage
from authentik.policies.engine import PolicyEngine

register = template.Library()


@register.simple_tag(takes_context=True)
# pylint: disable=unused-argument
def user_stages(context: RequestContext) -> dict[Stage, str]:
    """Return list of all stages which apply to user"""
    _all_stages: Iterable[Stage] = Stage.objects.all().select_subclasses()
    matching_stages: dict[Stage, str] = {}
    for stage in _all_stages:
        user_settings = stage.ui_user_settings
        if not user_settings:
            continue
        matching_stages[stage] = user_settings
    return matching_stages


@register.simple_tag(takes_context=True)
def user_sources(context: RequestContext) -> dict[Source, str]:
    """Return a list of all sources which are enabled for the user"""
    user = context.get("request").user
    _all_sources: Iterable[Source] = Source.objects.filter(
        enabled=True
    ).select_subclasses()
    matching_sources: dict[Source, str] = {}
    for source in _all_sources:
        user_settings = source.ui_user_settings
        if not user_settings:
            continue
        policy_engine = PolicyEngine(source, user, context.get("request"))
        policy_engine.build()
        if policy_engine.passing:
            matching_sources[source] = user_settings
    return matching_sources
