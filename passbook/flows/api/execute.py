"""Flow Execution API"""
from typing import List, Optional, Tuple

from django.http import Http404
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from structlog import get_logger

from passbook.core.models import Factor, User
from passbook.flows.api.serializers import (
    ChallengeCapabilities,
    ChallengeRequestSerializer,
    ChallengeResponseSerializer,
    InitiateFlowExecutionSerializer,
)
from passbook.flows.models import Flow
from passbook.lib.config import CONFIG

LOGGER = get_logger()

SESSION_PENDING_USER = "passbook_flows_pending_user"
SESSION_PENDING_FACTORS = "passbook_flows_pending_factors"


def get_user_by_uid(uid_value: str) -> Optional[User]:
    """Find user instance. Returns None if no user was found."""
    for search_field in CONFIG.y("passbook.uid_fields"):
        # Workaround for E-Mail -> email
        if search_field == "e-mail":
            search_field = "email"
        users = User.objects.filter(**{search_field: uid_value})
        if users.exists():
            LOGGER.debug("Found user", user=users.first(), uid_field=search_field)
            return users.first()
    return None


class FlowsExecuteViewSet(ViewSet):
    """Views to execute flows"""

    authentication_classes = []
    queryset = Flow.objects.none()
    http_method_names = ["get", "put", "post"]

    pending_flow: Flow
    pending_user: User

    @swagger_auto_schema(
        methods=["PUT"],
        request_body=InitiateFlowExecutionSerializer,
        responses={201: "Successfully initiated Flow Execution", 404: "UID not found."},
    )
    @action(methods=["PUT"], detail=True)
    def initiate(self, request: Request, pk) -> Response:
        # lookup flow, save pk, 404 if not found
        self.pending_flow = get_object_or_404(Flow, id=pk)
        # Get user by UID, save pk, 404 if not found
        req = InitiateFlowExecutionSerializer(data=request.data)
        if not req.is_valid():
            return Response(req.errors)
        self.pending_user = get_user_by_uid(req.validated_data.get("user_identifier"))
        if not self.pending_user:
            raise Http404
        # save list of factors of flow, in order

    @swagger_auto_schema(
        methods=["GET"], responses={200: ChallengeRequestSerializer(many=False)}
    )
    @swagger_auto_schema(methods=["POST"], request_body=ChallengeResponseSerializer)
    @action(methods=["GET", "POST"], detail=True)
    def challenge(self, request: Request, pk) -> Response:
        # 404 if not initiated
        if request.method.lower() == "post":
            return self.resolve_challenge(request, pk)
        return self.get_challenge(request, pk)

    def get_challenge(self, request: Request, pk) -> Response:
        # pop next factor off of queued factors
        # load pending user and factor
        # check if policy applies
        # return challenge
        pass

    def resolve_challenge(self, request: Request, pk) -> Response:
        # load next factor from queue
        # initialise with pending_user and request
        # user_ok or user_fail
        pass

    def get_pending_factors(self) -> List[Factor]:
        """Loading pending factors from Database or load from session variable"""
        # Write pending factors to session
        if SESSION_PENDING_FACTORS in self.request.session:
            return self.request.session[SESSION_PENDING_FACTORS]
        # Get an initial list of factors which are currently enabled
        # and apply to the current user. We check policies here and block the request
        _all_factors = (
            Factor.objects.filter(enabled=True).order_by("order").select_subclasses()
        )
        pending_factors = []
        for factor in _all_factors:
            LOGGER.debug(
                "Checking if factor applies to user",
                factor=factor,
                user=self.pending_user,
            )
            policy_engine = PolicyEngine(
                factor.policies.all(), self.pending_user, self.request
            )
            policy_engine.build()
            if policy_engine.passing:
                pending_factors.append((factor.uuid.hex, factor.type))
                LOGGER.debug("Factor applies", factor=factor, user=self.pending_user)
        return pending_factors
