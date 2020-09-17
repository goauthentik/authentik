"""passbook admin Middleware to impersonate users"""

from typing import Callable

from django.http import HttpRequest, HttpResponse

SESSION_IMPERSONATE_USER = "passbook_impersonate_user"
SESSION_IMPERSONATE_ORIGINAL_USER = "passbook_impersonate_original_user"


class ImpersonateMiddleware:
    """Middleware to impersonate users"""

    get_response: Callable[[HttpRequest], HttpResponse]

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # No permission checks are done here, they need to be checked before
        # SESSION_IMPERSONATE_USER is set.

        if SESSION_IMPERSONATE_USER in request.session:
            request.user = request.session[SESSION_IMPERSONATE_USER]

        return self.get_response(request)
