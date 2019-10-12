"""YAML fields"""
import yaml
from django import forms
from django.utils.translation import gettext_lazy as _


class InvalidYAMLInput(str):
    """Invalid YAML String type"""


class YAMLString(str):
    """YAML String type"""


class YAMLField(forms.CharField):
    """Django's JSON Field converted to YAML"""

    default_error_messages = {
        'invalid': _("'%(value)s' value must be valid YAML."),
    }
    widget = forms.Textarea

    def to_python(self, value):
        if self.disabled:
            return value
        if value in self.empty_values:
            return None
        if isinstance(value, (list, dict, int, float, YAMLString)):
            return value
        try:
            converted = yaml.safe_load(value)
        except yaml.YAMLError:
            raise forms.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )
        if isinstance(converted, str):
            return YAMLString(converted)
        return converted

    def bound_data(self, data, initial):
        if self.disabled:
            return initial
        try:
            return yaml.safe_load(data)
        except yaml.YAMLError:
            return InvalidYAMLInput(data)

    def prepare_value(self, value):
        if isinstance(value, InvalidYAMLInput):
            return value
        return yaml.dump(value, explicit_start=True)

    def has_changed(self, initial, data):
        if super().has_changed(initial, data):
            return True
        # For purposes of seeing whether something has changed, True isn't the
        # same as 1 and the order of keys doesn't matter.
        data = self.to_python(data)
        return yaml.dump(initial, sort_keys=True) != yaml.dump(data, sort_keys=True)
