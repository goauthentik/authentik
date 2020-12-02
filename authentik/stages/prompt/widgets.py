"""Prompt Widgets"""
from django import forms
from django.utils.safestring import mark_safe


class StaticTextWidget(forms.widgets.Widget):
    """Widget to render static text"""

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(f"<p>{value}</p>")  # nosec


class HorizontalRuleWidget(forms.widgets.Widget):
    """Widget, which renders an <hr> element"""

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe("<hr>")  # nosec
