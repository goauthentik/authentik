"""policy API Views"""
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
)
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.utils import (
    CacheSerializer,
    MetaNameSerializer,
    TypeCreateSerializer,
)
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses
from authentik.policies.models import Policy, PolicyBinding, PolicyBindingModel


class PolicyBindingModelForeignKey(PrimaryKeyRelatedField):
    """rest_framework PrimaryKeyRelatedField which resolves
    model_manager's InheritanceQuerySet"""

    def use_pk_only_optimization(self):
        return False

    # pylint: disable=inconsistent-return-statements
    def to_internal_value(self, data):
        if self.pk_field is not None:
            data = self.pk_field.to_internal_value(data)
        try:
            # Due to inheritance, a direct DB lookup for the primary key
            # won't return anything. This is because the direct lookup
            # checks the PK of PolicyBindingModel (for example),
            # but we get given the Primary Key of the inheriting class
            for model in self.get_queryset().select_subclasses().all().select_related():
                if model.pk == data:
                    return model
            # as a fallback we still try a direct lookup
            return self.get_queryset().get_subclass(pk=data)
        except ObjectDoesNotExist:
            self.fail("does_not_exist", pk_value=data)
        except (TypeError, ValueError):
            self.fail("incorrect_type", data_type=type(data).__name__)

    def to_representation(self, value):
        correct_model = PolicyBindingModel.objects.get_subclass(pbm_uuid=value.pbm_uuid)
        return correct_model.pk


class PolicySerializer(ModelSerializer, MetaNameSerializer):
    """Policy Serializer"""

    _resolve_inheritance: bool

    object_type = SerializerMethodField()
    bound_to = SerializerMethodField()

    def __init__(self, *args, resolve_inheritance: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._resolve_inheritance = resolve_inheritance

    def get_object_type(self, obj: Policy) -> str:
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("policy", "")

    def get_bound_to(self, obj: Policy) -> int:
        """Return objects policy is bound to"""
        if not obj.bindings.exists() and not obj.promptstage_set.exists():
            return 0
        return obj.bindings.count()

    def to_representation(self, instance: Policy):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == Policy or not self._resolve_inheritance:
            return super().to_representation(instance)
        return dict(
            instance.serializer(instance=instance, resolve_inheritance=False).data
        )

    class Meta:

        model = Policy
        fields = [
            "pk",
            "name",
            "execution_logging",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
            "bound_to",
        ]
        depth = 3


class PolicyViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Policy Viewset"""

    queryset = Policy.objects.all()
    serializer_class = PolicySerializer
    filterset_fields = {
        "bindings": ["isnull"],
        "promptstage": ["isnull"],
    }
    search_fields = ["name"]

    def get_queryset(self):
        return Policy.objects.select_subclasses().prefetch_related(
            "bindings", "promptstage_set"
        )

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable policy types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:policy-create")
                    + f"?type={subclass.__name__}",
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @swagger_auto_schema(responses={200: CacheSerializer(many=False)})
    @action(detail=False)
    def cached(self, request: Request) -> Response:
        """Info about cached policies"""
        return Response(data={"count": len(cache.keys("policy_*"))})


class PolicyBindingSerializer(ModelSerializer):
    """PolicyBinding Serializer"""

    # Because we're not interested in the PolicyBindingModel's PK but rather the subclasses PK,
    # we have to manually declare this field
    target = PolicyBindingModelForeignKey(
        queryset=PolicyBindingModel.objects.select_subclasses(),
        required=True,
    )

    class Meta:

        model = PolicyBinding
        fields = [
            "pk",
            "policy",
            "group",
            "user",
            "target",
            "enabled",
            "order",
            "timeout",
        ]
        depth = 2


class PolicyBindingViewSet(ModelViewSet):
    """PolicyBinding Viewset"""

    queryset = PolicyBinding.objects.all().select_related(
        "policy", "target", "group", "user"
    )
    serializer_class = PolicyBindingSerializer
    filterset_fields = ["policy", "target", "enabled", "order", "timeout"]
    search_fields = ["policy__name"]
