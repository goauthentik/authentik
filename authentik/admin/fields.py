"""Additional fields"""
import yaml
from django import forms
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _


class ArrayFieldSelectMultiple(forms.SelectMultiple):
    """This is a Form Widget for use with a Postgres ArrayField. It implements
    a multi-select interface that can be given a set of `choices`.
    You can provide a `delimiter` keyword argument to specify the delimeter used.

    https://gist.github.com/stephane/00e73c0002de52b1c601"""

    def __init__(self, *args, **kwargs):
        # Accept a `delimiter` argument, and grab it (defaulting to a comma)
        self.delimiter = kwargs.pop("delimiter", ",")
        super().__init__(*args, **kwargs)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            # Normally, we'd want a list here, which is what we get from the
            # SelectMultiple superclass, but the SimpleArrayField expects to
            # get a delimited string, so we're doing a little extra work.
            return self.delimiter.join(data.getlist(name))

        return data.get(name)

    def get_context(self, name, value, attrs):
        return super().get_context(name, value.split(self.delimiter), attrs)


class CodeMirrorWidget(forms.Textarea):
    """Custom Textarea-based Widget that triggers a CodeMirror editor"""

    # CodeMirror mode to enable
    mode: str

    template_name = "fields/codemirror.html"

    def __init__(self, *args, mode="yaml", **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode

    def render(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["mode"] = self.mode
        return super().render(*args, **kwargs)


class InvalidYAMLInput(str):
    """Invalid YAML String type"""


class YAMLString(str):
    """YAML String type"""


class YAMLField(forms.JSONField):
    """Django's JSON Field converted to YAML"""

    default_error_messages = {
        "invalid": _("'%(value)s' value must be valid YAML."),
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
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            )
        if isinstance(converted, str):
            return YAMLString(converted)
        if converted is None:
            return {}
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
        return yaml.dump(value, explicit_start=True, default_flow_style=False)

    def has_changed(self, initial, data):
        if super().has_changed(initial, data):
            return True
        # For purposes of seeing whether something has changed, True isn't the
        # same as 1 and the order of keys doesn't matter.
        data = self.to_python(data)
        return yaml.dump(initial, sort_keys=True) != yaml.dump(data, sort_keys=True)
