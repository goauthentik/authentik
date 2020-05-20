"""passbook Expression Policy forms"""

from django import forms

from passbook.admin.fields import CodeMirrorWidget
from passbook.policies.expression.models import ExpressionPolicy
from passbook.policies.forms import GENERAL_FIELDS


class ExpressionPolicyForm(forms.ModelForm):
    """ExpressionPolicy Form"""

    template_name = "policy/expression/form.html"

    class Meta:

        model = ExpressionPolicy
        fields = GENERAL_FIELDS + [
            "expression",
        ]
        widgets = {
            "name": forms.TextInput(),
            "expression": CodeMirrorWidget(mode="jinja2"),
        }
