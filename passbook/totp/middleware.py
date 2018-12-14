"""passbook TOTP Middleware to force users with TOTP set up to verify"""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django_otp import user_has_device


def totp_force_verify(get_response):
    """Middleware to force TOTP Verification"""

    def middleware(request):
        """Middleware to force TOTP Verification"""

        # pylint: disable=too-many-boolean-expressions
        if request.user.is_authenticated and \
                user_has_device(request.user) and \
                not request.user.is_verified() and \
                request.path != reverse('passbook_totp:totp-verify') and \
                request.path != reverse('account-logout') and \
                not request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer'):
            # User has TOTP set up but is not verified

            # At this point the request is already forwarded to the target destination
            # So we just add the current request's path as next parameter
            args = '?%s' % urlencode({'next': request.get_full_path()})
            return redirect(reverse('passbook_totp:totp-verify') + args)

        response = get_response(request)
        return response

    return middleware
