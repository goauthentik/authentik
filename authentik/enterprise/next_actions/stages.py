"""Required-action extensions for login and flow redirects."""

from django.contrib import messages
from django.utils.translation import gettext as _

from authentik.enterprise.license import LicenseKey
from authentik.enterprise.models import LicenseUsageStatus
from authentik.enterprise.next_actions import USER_ATTRIBUTE_NEXT_ACTIONS
from authentik.enterprise.next_actions.flows import (
    NEXT_ACTION_DISALLOWED_DESIGNATIONS,
    SESSION_KEY_PENDING_NEXT_ACTIONS,
    NextActionDoneStageView,
)
from authentik.flows.models import Flow
from authentik.flows.planner import PLAN_CONTEXT_REDIRECT, PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION
from authentik.flows.views.executor import SESSION_KEY_PLAN, InvalidStageError


class NextActionsLoginMixin:
    """Flag required actions after a successful login."""

    def cleanup(self):
        super().cleanup()
        user = self.request.user
        if (
            PLAN_CONTEXT_USER_SWITCH_TARGET_SESSION not in self.executor.plan.context
            and USER_ATTRIBUTE_NEXT_ACTIONS in user.attributes
            and user.attributes[USER_ATTRIBUTE_NEXT_ACTIONS] != []
            # Expiry must not release a required action.
            and LicenseKey.cached_summary().status != LicenseUsageStatus.UNLICENSED
        ):
            self.request.session[SESSION_KEY_PENDING_NEXT_ACTIONS] = True
            messages.info(
                self.request,
                _("Login successful. Complete the required actions before continuing."),
            )


class NextActionsRedirectMixin:
    """Keep required-action completion across flow handoffs."""

    def switch_flow_with_context(self, flow: Flow, keep_context=True) -> str:
        completion = next(
            (
                binding
                for binding in self.executor.plan.bindings
                if binding.stage.view is NextActionDoneStageView
            ),
            None,
        )
        if completion and flow.designation in NEXT_ACTION_DISALLOWED_DESIGNATIONS:
            raise InvalidStageError(_("Required actions cannot redirect to login or logout flows."))
        redirect_to = super().switch_flow_with_context(flow, keep_context)
        plan = self.request.session[SESSION_KEY_PLAN]
        if completion:
            plan.append(completion)
            if PLAN_CONTEXT_REDIRECT in self.executor.plan.context:
                plan.context[PLAN_CONTEXT_REDIRECT] = self.executor.plan.context[
                    PLAN_CONTEXT_REDIRECT
                ]
        return redirect_to
