"""passbook admin Middleware to impersonate users"""

from passbook.core.models import User


def impersonate(get_response):
    """Middleware to impersonate users"""

    def middleware(request):
        """Middleware to impersonate users"""

        # User is superuser and has __impersonate ID set
        if request.user.is_superuser and "__impersonate" in request.GET:
            request.session["impersonate_id"] = request.GET["__impersonate"]
        # user wants to stop impersonation
        elif "__unimpersonate" in request.GET and "impersonate_id" in request.session:
            del request.session["impersonate_id"]

        # Actually impersonate user
        if request.user.is_superuser and "impersonate_id" in request.session:
            request.user = User.objects.get(pk=request.session["impersonate_id"])

        response = get_response(request)
        return response

    return middleware
