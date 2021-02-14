from django.http import HttpRequest, HttpResponse, JsonResponse
from django.http.response import HttpResponseBadRequest
from django.views import View
from structlog.stdlib import get_logger
from webauthn import (
    WebAuthnAssertionOptions,
    WebAuthnAssertionResponse,
    WebAuthnMakeCredentialOptions,
    WebAuthnRegistrationResponse,
    WebAuthnUser,
)

from authentik.core.models import User
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.views import SESSION_KEY_PLAN
from authentik.lib.templatetags.authentik_utils import avatar
from authentik.stages.webauthn.models import WebAuthnDevice
from authentik.stages.webauthn.utils import generate_challenge

LOGGER = get_logger()
RP_ID = "localhost"
RP_NAME = "authentik"
ORIGIN = "http://localhost:8000"


class FlowUserRequiredView(View):

    user: User

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        plan = request.session.get(SESSION_KEY_PLAN, None)
        if not plan:
            return HttpResponseBadRequest()
        self.user = plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not self.user:
            return HttpResponseBadRequest()
        return super().dispatch(request, *args, **kwargs)


class BeginActivateView(FlowUserRequiredView):
    def post(self, request: HttpRequest) -> HttpResponse:
        # clear session variables prior to starting a new registration
        request.session.pop("challenge", None)

        challenge = generate_challenge(32)

        # We strip the saved challenge of padding, so that we can do a byte
        # comparison on the URL-safe-without-padding challenge we get back
        # from the browser.
        # We will still pass the padded version down to the browser so that the JS
        # can decode the challenge into binary without too much trouble.
        request.session["challenge"] = challenge.rstrip("=")

        make_credential_options = WebAuthnMakeCredentialOptions(
            challenge,
            RP_NAME,
            RP_ID,
            self.user.uid,
            self.user.username,
            self.user.name,
            avatar(self.user),
        )

        return JsonResponse(make_credential_options.registration_dict)


class BeginAssertion(FlowUserRequiredView):
    def post(self, request: HttpRequest) -> HttpResponse:
        request.session.pop("challenge", None)

        challenge = generate_challenge(32)

        # We strip the padding from the challenge stored in the session
        # for the reasons outlined in the comment in webauthn_begin_activate.
        request.session["challenge"] = challenge.rstrip("=")

        device = WebAuthnDevice.objects.first()

        webauthn_user = WebAuthnUser(
            self.user.uid,
            self.user.username,
            self.user.name,
            avatar(self.user),
            device.credential_id,
            device.pubkey,
            device.sign_count,
            device.rp_id,
        )

        webauthn_assertion_options = WebAuthnAssertionOptions(webauthn_user, challenge)

        return JsonResponse(webauthn_assertion_options.assertion_dict)


class VerifyCredentialInfo(FlowUserRequiredView):
    def post(self, request: HttpRequest) -> HttpResponse:
        challenge = request.session["challenge"]

        registration_response = request.POST
        trusted_attestation_cert_required = True
        self_attestation_permitted = True
        none_attestation_permitted = True

        webauthn_registration_response = WebAuthnRegistrationResponse(
            RP_ID,
            ORIGIN,
            registration_response,
            challenge,
            trusted_attestation_cert_required=trusted_attestation_cert_required,
            self_attestation_permitted=self_attestation_permitted,
            none_attestation_permitted=none_attestation_permitted,
            uv_required=False,
        )  # User Verification

        try:
            webauthn_credential = webauthn_registration_response.verify()
        except Exception as exc:
            LOGGER.warning("registration failed", exc=exc)
            return JsonResponse({"fail": "Registration failed. Error: {}".format(exc)})

        # Step 17.
        #
        # Check that the credentialId is not yet registered to any other user.
        # If registration is requested for a credential that is already registered
        # to a different user, the Relying Party SHOULD fail this registration
        # ceremony, or it MAY decide to accept the registration, e.g. while deleting
        # the older registration.
        credential_id_exists = WebAuthnDevice.objects.filter(
            credential_id=webauthn_credential.credential_id
        ).first()
        if credential_id_exists:
            return JsonResponse({"fail": "Credential ID already exists."}, status=401)

        webauthn_credential.credential_id = str(
            webauthn_credential.credential_id, "utf-8"
        )
        webauthn_credential.public_key = str(webauthn_credential.public_key, "utf-8")
        existing_device = WebAuthnDevice.objects.filter(
            credential_id=webauthn_credential.credential_id
        ).first()
        if not existing_device:
            user = WebAuthnDevice.objects.create(
                user=self.user,
                public_key=webauthn_credential.public_key,
                credential_id=webauthn_credential.credential_id,
                sign_count=webauthn_credential.sign_count,
                rp_id=RP_ID,
            )
        else:
            return JsonResponse({"fail": "User already exists."}, status=401)

        LOGGER.debug("Successfully registered.", user=user)

        return JsonResponse({"success": "User successfully registered."})


class VerifyAssertion(FlowUserRequiredView):
    def post(self, request: HttpRequest) -> HttpResponse:
        challenge = request.session.get("challenge")
        assertion_response = request.form
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
            device.pub_key,
            device.sign_count,
            device.user.rp_id,
        )

        webauthn_assertion_response = WebAuthnAssertionResponse(
            webauthn_user, assertion_response, challenge, ORIGIN, uv_required=False
        )  # User Verification

        try:
            sign_count = webauthn_assertion_response.verify()
        except Exception as e:
            return JsonResponse({"fail": "Assertion failed. Error: {}".format(e)})

        device.set_sign_count(sign_count)

        return JsonResponse(
            {"success": "Successfully authenticated as {}".format(self.user.username)}
        )
