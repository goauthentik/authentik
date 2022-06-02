"""policy API Views"""
from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_objects_for_user
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger
from structlog.testing import capture_logs

from authentik.api.decorators import permission_required
from authentik.core.api.applications import user_app_cache_key
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import CacheSerializer, MetaNameSerializer, TypeCreateSerializer
from authentik.events.utils import sanitize_dict
from authentik.lib.utils.reflection import all_subclasses
from authentik.policies.api.exec import PolicyTestResultSerializer, PolicyTestSerializer
from authentik.policies.models import Policy, PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.policies.types import PolicyRequest

LOGGER = get_logger()


class PolicySerializer(ModelSerializer, MetaNameSerializer):
    """Policy Serializer"""

    _resolve_inheritance: bool

    component = SerializerMethodField()
    bound_to = SerializerMethodField()

    def __init__(self, *args, resolve_inheritance: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._resolve_inheritance = resolve_inheritance

    def get_component(self, obj: Policy) -> str:  # pragma: no cover
        """Get object component so that we know how to edit the object"""
        # pyright: reportGeneralTypeIssues=false
        if obj.__class__ == Policy:
            return ""
        return obj.component

    def get_bound_to(self, obj: Policy) -> int:
        """Return objects policy is bound to"""
        return obj.bindings.count() + obj.promptstage_set.count()

    def to_representation(self, instance: Policy):
        # pyright: reportGeneralTypeIssues=false
        if instance.__class__ == Policy or not self._resolve_inheritance:
            return super().to_representation(instance)
        return dict(instance.serializer(instance=instance, resolve_inheritance=False).data)

    class Meta:

        model = Policy
        fields = [
            "pk",
            "name",
            "execution_logging",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "bound_to",
        ]
        depth = 3


class PolicyViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
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
    ordering = ["name"]

    def get_queryset(self):  # pragma: no cover
        return Policy.objects.select_subclasses().prefetch_related("bindings", "promptstage_set")

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def types(self, request: Request) -> Response:
        """Get all creatable policy types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            subclass: Policy
            data.append(
                {
                    "name": subclass._meta.verbose_name,
                    "description": subclass.__doc__,
                    "component": subclass().component,
                    "model_name": subclass._meta.model_name,
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @permission_required(None, ["authentik_policies.view_policy_cache"])
    @extend_schema(responses={200: CacheSerializer(many=False)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def cache_info(self, request: Request) -> Response:
        """Info about cached policies"""
        return Response(data={"count": len(cache.keys("policy_*"))})

    @permission_required(None, ["authentik_policies.clear_policy_cache"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Successfully cleared cache"),
            400: OpenApiResponse(description="Bad request"),
        },
    )
    @action(detail=False, methods=["POST"])
    def cache_clear(self, request: Request) -> Response:
        """Clear policy cache"""
        keys = cache.keys("policy_*")
        cache.delete_many(keys)
        LOGGER.debug("Cleared Policy cache", keys=len(keys))
        # Also delete user application cache
        keys = cache.keys(user_app_cache_key("*"))
        cache.delete_many(keys)
        return Response(status=204)

    @permission_required("authentik_policies.view_policy")
    @extend_schema(
        request=PolicyTestSerializer(),
        responses={
            200: PolicyTestResultSerializer(),
            400: OpenApiResponse(description="Invalid parameters"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    # pylint: disable=unused-argument, invalid-name
    def test(self, request: Request, pk: str) -> Response:
        """Test policy"""
        policy = self.get_object()
        test_params = PolicyTestSerializer(data=request.data)
        if not test_params.is_valid():
            return Response(test_params.errors, status=400)

        # User permission check, only allow policy testing for users that are readable
        users = get_objects_for_user(request.user, "authentik_core.view_user").filter(
            pk=test_params.validated_data["user"].pk
        )
        if not users.exists():
            raise PermissionDenied()

        p_request = PolicyRequest(users.first())
        p_request.debug = True
        p_request.set_http_request(self.request)
        p_request.context = test_params.validated_data.get("context", {})

        proc = PolicyProcess(PolicyBinding(policy=policy), p_request, None)
        with capture_logs() as logs:
            result = proc.execute()
        log_messages = []
        for log in logs:
            if log.get("process", "") == "PolicyProcess":
                continue
            log_messages.append(sanitize_dict(log))
        result.log_messages = log_messages
        response = PolicyTestResultSerializer(result)
        return Response(response.data)
