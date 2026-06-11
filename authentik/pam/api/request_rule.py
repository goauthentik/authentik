from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.pam.models import PolicyBindingModelRequestRule


class PolicyBindingModelRequestRuleSerializer(ModelSerializer):

    class Meta:
        model = PolicyBindingModelRequestRule
        fields = "__all__"


class PolicyBindingModelRequestRuleViewSet(ModelViewSet):

    queryset = PolicyBindingModelRequestRule.objects.all()
    serializer_class = PolicyBindingModelRequestRuleSerializer
