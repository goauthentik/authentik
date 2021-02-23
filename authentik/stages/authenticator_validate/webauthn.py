from webauthn import WebAuthnAssertionOptions, WebAuthnAssertionResponse, WebAuthnUser
from webauthn.webauthn import (
    AuthenticationRejectedException,
    RegistrationRejectedException,
    WebAuthnUserDataMissing,
)

class BeginAssertion(FlowUserRequiredView):
    """Send the client a challenge that we'll check later"""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Send the client a challenge that we'll check later"""
        request.session.pop("challenge", None)

        challenge = generate_challenge(32)

        # We strip the padding from the challenge stored in the session
        # for the reasons outlined in the comment in webauthn_begin_activate.
        request.session["challenge"] = challenge.rstrip("=")

        devices = WebAuthnDevice.objects.filter(user=self.user)
        if not devices.exists():
            return HttpResponseBadRequest()
        device: WebAuthnDevice = devices.first()

        webauthn_user = WebAuthnUser(
            self.user.uid,
            self.user.username,
            self.user.name,
            avatar(self.user),
            device.credential_id,
            device.public_key,
            device.sign_count,
            device.rp_id,
        )

        webauthn_assertion_options = WebAuthnAssertionOptions(webauthn_user, challenge)

        return JsonResponse(webauthn_assertion_options.assertion_dict)


class VerifyAssertion(FlowUserRequiredView):
    """Verify assertion result that we've sent to the client"""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Verify assertion result that we've sent to the client"""
        challenge = request.session.get("challenge")
        assertion_response = request.POST
        credential_id = assertion_response.get("id")

        device = WebAuthnDevice.objects.filter(credential_id=credential_id).first()
        if not device:
            return JsonResponse({"fail": "Device does not exist."}, status=401)

        webauthn_user = WebAuthnUser(
            self.user.uid,
            self.user.username,
            self.user.name,
            avatar(self.user),
            device.credential_id,
            device.public_key,
            device.sign_count,
            device.rp_id,
        )

        webauthn_assertion_response = WebAuthnAssertionResponse(
            webauthn_user, assertion_response, challenge, ORIGIN, uv_required=False
        )  # User Verification

        try:
            sign_count = webauthn_assertion_response.verify()
        except (
            AuthenticationRejectedException,
            WebAuthnUserDataMissing,
            RegistrationRejectedException,
        ) as exc:
            return JsonResponse({"fail": "Assertion failed. Error: {}".format(exc)})

        device.set_sign_count(sign_count)
        request.session[SESSION_KEY_WEBAUTHN_AUTHENTICATED] = True
        return JsonResponse(
            {"success": "Successfully authenticated as {}".format(self.user.username)}
        )
