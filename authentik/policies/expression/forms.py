"""authentik Expression Policy forms"""

from django import forms

from authentik.admin.fields import CodeMirrorWidget
from authentik.policies.expression.evaluator import PolicyEvaluator
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.forms import PolicyForm


class ExpressionPolicyForm(PolicyForm):
    """ExpressionPolicy Form"""

    template_name = "policy/expression/form.html"

    def clean_expression(self):
        """Test Syntax"""
        expression = self.cleaned_data.get("expression")
        PolicyEvaluator(self.instance.name).validate(expression)
        return expression

    class Meta:

        model = ExpressionPolicy
        fields = PolicyForm.Meta.fields + [
            "expression",
        ]
        widgets = {
            "name": forms.TextInput(),
            "expression": CodeMirrorWidget(mode="python"),
        }
