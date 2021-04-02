"""Additional fields"""
from django import forms
from django.utils.datastructures import MultiValueDict


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
