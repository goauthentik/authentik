"""password stage views"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from passbook.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner
from passbook.flows.views import SESSION_KEY_PLAN
from passbook.lib.utils.urls import redirect_with_qs
from passbook.stages.password.models import PasswordStage

