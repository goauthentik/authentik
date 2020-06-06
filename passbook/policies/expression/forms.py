"""passbook Expression Policy forms"""

from django import forms

from passbook.admin.fields import CodeMirrorWidget
from passbook.policies.expression.evaluator import PolicyEvaluator
from passbook.policies.expression.models import ExpressionPolicy
from passbook.policies.forms import GENERAL_FIELDS


class ExpressionPolicyForm(forms.ModelForm):
    """ExpressionPolicy Form"""

    template_name = "policy/expression/form.html"

    def clean_expression(self):
        """Test Syntax"""
        expression = self.cleaned_data.get("expression")
        PolicyEvaluator(self.instance.name).validate(expression)
        return expression

    class Meta:

        model = ExpressionPolicy
        fields = GENERAL_FIELDS + [
            "expression",
        ]
        widgets = {
            "name": forms.TextInput(),
            "expression": CodeMirrorWidget(mode="python"),
        }
