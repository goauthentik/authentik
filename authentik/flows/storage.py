from copy import deepcopy
from typing import Self

from django.http import HttpRequest, QueryDict

from authentik.flows.planner import FlowPlan

SESSION_KEY_PLAN = "authentik/flows/plan"
SESSION_KEY_GET = "authentik/flows/get"
SESSION_KEY_POST = "authentik/flows/post"
SESSION_KEY_HISTORY = "authentik/flows/history"


class FlowExecution:
    """State of the flow the request's session is currently executing.

    Values are loaded once on creation; change them through the operation
    methods, or set the attributes directly and call `save()`."""

    def __init__(self, request: HttpRequest):
        self.request = request
        session = request.session
        self.plan: FlowPlan | None = session.get(SESSION_KEY_PLAN)
        # Query parameters the flow was started with
        self.query: QueryDict = session.get(SESSION_KEY_GET) or QueryDict()
        # POST body of the request that triggered the flow (SAML POST binding)
        self.post: QueryDict | None = session.get(SESSION_KEY_POST)
        # Previous states of the plan, only used by the flow inspector
        self.history: list[FlowPlan] = session.get(SESSION_KEY_HISTORY, [])

    @classmethod
    def start(cls, request: HttpRequest, plan: FlowPlan, query: QueryDict | None = None) -> Self:
        """Start a fresh execution, dropping the history of the previous one.
        The POST body is kept, as it was saved before the flow was started."""
        execution = cls(request)
        execution.plan = plan
        execution.history = []
        if query is not None:
            execution.query = query
        execution.save()
        return execution

    def replace(self, plan: FlowPlan):
        """Replace the plan, keeping history and query parameters"""
        self.plan = plan
        self.save()

    def advance(self):
        """Record the current plan in the history and continue to the next stage"""
        self.history.append(deepcopy(self.plan))
        self.plan.pop()
        self.save()

    def pop_post(self) -> QueryDict | None:
        """Get and remove the saved POST body"""
        post, self.post = self.post, None
        self.save()
        return post

    def clear(self):
        """Drop the plan only, i.e. when it belongs to a different flow"""
        self.plan = None
        self.save()

    def cancel(self):
        """Stop the execution. History is kept as the inspector might still read it,
        the POST body is kept as later requests might still need it."""
        self.plan = None
        self.query = QueryDict()
        self.save()

    def save(self):
        """Write the state to the request's current session"""
        session = self.request.session
        for key, value in (
            (SESSION_KEY_PLAN, self.plan),
            (SESSION_KEY_GET, self.query),
            (SESSION_KEY_POST, self.post),
            (SESSION_KEY_HISTORY, self.history),
        ):
            if value is None or (key == SESSION_KEY_GET and not value):
                session.pop(key, None)
            else:
                session[key] = value
