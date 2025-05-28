from binascii import hexlify
from urllib.parse import unquote_plus

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.x509 import (
    Certificate,
    NameOID,
    ObjectIdentifier,
    UnsupportedGeneralNameType,
    load_pem_x509_certificate,
)
from cryptography.x509.verification import PolicyBuilder, Store, VerificationError
from django.utils.translation import gettext_lazy as _

from authentik.brands.models import Brand
from authentik.core.models import User
from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.stages.mtls.models import (
    CertAttributes,
    MutualTLSStage,
    TLSMode,
    UserAttributes,
)
from authentik.flows.challenge import AccessDeniedChallenge
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.root.middleware import ClientIPMiddleware
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

# All of these headers must only be accepted from "trusted" reverse proxies
# See internal/web/proxy.go:39
HEADER_PROXY_FORWARDED = "X-Forwarded-Client-Cert"
HEADER_NGINX_FORWARDED = "SSL-Client-Cert"
HEADER_TRAEFIK_FORWARDED = "X-Forwarded-TLS-Client-Cert"
HEADER_OUTPOST_FORWARDED = "X-Authentik-Outpost-Certificate"


PLAN_CONTEXT_CERTIFICATE = "certificate"


class MTLSStageView(ChallengeStageView):

    def __parse_single_cert(self, raw: str | None) -> list[Certificate]:
        """Helper to parse a single certificate"""
        if not raw:
            return []
        try:
            cert = load_pem_x509_certificate(unquote_plus(raw).encode())
            return [cert]
        except ValueError as exc:
            self.logger.info("Failed to parse certificate", exc=exc)
            return []

    def _parse_cert_xfcc(self) -> list[Certificate]:
        """Parse certificates in the format given to us in
        the format of the authentik router/envoy"""
        xfcc_raw = self.request.headers.get(HEADER_PROXY_FORWARDED)
        if not xfcc_raw:
            return []
        certs = []
        for r_cert in xfcc_raw.split(","):
            el = r_cert.split(";")
            raw_cert = {k.split("=")[0]: k.split("=")[1] for k in el}
            if "Cert" not in raw_cert:
                continue
            certs.extend(self.__parse_single_cert(raw_cert["Cert"]))
        return certs

    def _parse_cert_nginx(self) -> list[Certificate]:
        """Parse certificates in the format nginx-ingress gives to us"""
        sslcc_raw = self.request.headers.get(HEADER_NGINX_FORWARDED)
        return self.__parse_single_cert(sslcc_raw)

    def _parse_cert_traefik(self) -> list[Certificate]:
        """Parse certificates in the format traefik gives to us"""
        ftcc_raw = self.request.headers.get(HEADER_TRAEFIK_FORWARDED)
        return self.__parse_single_cert(ftcc_raw)

    def _parse_cert_outpost(self) -> list[Certificate]:
        """Parse certificates in the format outposts give to us. Also authenticates
        the outpost to ensure it has the permission to do so"""
        user = ClientIPMiddleware.get_outpost_user(self.request)
        if not user:
            return []
        if not user.has_perm(
            "pass_outpost_certificate", self.executor.current_stage
        ) and not user.has_perm("authentik_stages_mtls.pass_outpost_certificate"):
            return []
        outpost_raw = self.request.headers.get(HEADER_OUTPOST_FORWARDED)
        return self.__parse_single_cert(outpost_raw)

    def get_authorities(self) -> list[CertificateKeyPair] | None:
        # We can't access `certificate_authorities` on `self.executor.current_stage`, as that would
        # load the certificate into the directly referenced foreign key, which we have to pickle
        # as part of the flow plan, and cryptography certs can't be pickled
        stage: MutualTLSStage = (
            MutualTLSStage.objects.filter(pk=self.executor.current_stage.pk)
            .prefetch_related("certificate_authorities")
            .first()
        )
        if stage.certificate_authorities.exists():
            return stage.certificate_authorities.order_by("name")
        brand: Brand = self.request.brand
        if brand.client_certificates.exists():
            return brand.client_certificates.order_by("name")
        return None

    def validate_cert(self, authorities: list[CertificateKeyPair], certs: list[Certificate]):
        authorities_cert = [x.certificate for x in authorities]
        for _cert in certs:
            try:
                PolicyBuilder().store(Store(authorities_cert)).build_client_verifier().verify(
                    _cert, []
                )
                return _cert
            except (
                InvalidSignature,
                TypeError,
                ValueError,
                VerificationError,
                UnsupportedGeneralNameType,
            ) as exc:
                self.logger.warning("Discarding invalid certificate", cert=_cert, exc=exc)
                continue
        return None

    def check_if_user(self, cert: Certificate):
        stage: MutualTLSStage = self.executor.current_stage
        cert_attr = None
        user_attr = None
        match stage.cert_attribute:
            case CertAttributes.SUBJECT:
                cert_attr = cert.subject.rfc4514_string()
            case CertAttributes.COMMON_NAME:
                cert_attr = self.get_cert_attribute(cert, NameOID.COMMON_NAME)
            case CertAttributes.EMAIL:
                cert_attr = self.get_cert_attribute(cert, NameOID.EMAIL_ADDRESS)
        match stage.user_attribute:
            case UserAttributes.USERNAME:
                user_attr = "username"
            case UserAttributes.EMAIL:
                user_attr = "email"
        if not user_attr or not cert_attr:
            return None
        return User.objects.filter(**{user_attr: cert_attr}).first()

    def _cert_to_dict(self, cert: Certificate) -> dict:
        """Represent a certificate in a dictionary, as certificate objects cannot be pickled"""
        return {
            "serial_number": str(cert.serial_number),
            "subject": cert.subject.rfc4514_string(),
            "issuer": cert.issuer.rfc4514_string(),
            "fingerprint_sha256": hexlify(cert.fingerprint(hashes.SHA256()), ":").decode("utf-8"),
            "fingerprint_sha1": hexlify(cert.fingerprint(hashes.SHA1()), ":").decode(  # nosec
                "utf-8"
            ),
        }

    def auth_user(self, user: User, cert: Certificate):
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
        self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD, "mtls")
        self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].update(
            {"certificate": self._cert_to_dict(cert)}
        )

    def enroll_prepare_user(self, cert: Certificate):
        self.executor.plan.context.setdefault(PLAN_CONTEXT_PROMPT, {})
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(
            {
                "email": self.get_cert_attribute(cert, NameOID.EMAIL_ADDRESS),
                "name": self.get_cert_attribute(cert, NameOID.COMMON_NAME),
            }
        )
        self.executor.plan.context[PLAN_CONTEXT_CERTIFICATE] = self._cert_to_dict(cert)

    def get_cert_attribute(self, cert: Certificate, oid: ObjectIdentifier) -> str | None:
        attr = cert.subject.get_attributes_for_oid(oid)
        if len(attr) < 1:
            return None
        return str(attr[0].value)

    def dispatch(self, request, *args, **kwargs):
        stage: MutualTLSStage = self.executor.current_stage
        certs = [
            *self._parse_cert_xfcc(),
            *self._parse_cert_nginx(),
            *self._parse_cert_traefik(),
            *self._parse_cert_outpost(),
        ]
        authorities = self.get_authorities()
        if not authorities:
            self.logger.warning("No Certificate authority found")
            if stage.mode == TLSMode.OPTIONAL:
                return self.executor.stage_ok()
            if stage.mode == TLSMode.REQUIRED:
                return super().dispatch(request, *args, **kwargs)
        cert = self.validate_cert(authorities, certs)
        if not cert and stage.mode == TLSMode.REQUIRED:
            self.logger.warning("Client certificate required but no certificates given")
            return super().dispatch(
                request,
                *args,
                error_message=_("Certificate required but no certificate was given."),
                **kwargs,
            )
        if not cert and stage.mode == TLSMode.OPTIONAL:
            self.logger.info("No certificate given, continuing")
            return self.executor.stage_ok()
        existing_user = self.check_if_user(cert)
        if self.executor.flow.designation == FlowDesignation.ENROLLMENT:
            self.enroll_prepare_user(cert)
        elif existing_user:
            self.auth_user(existing_user, cert)
        else:
            return super().dispatch(
                request, *args, error_message=_("No user found for certificate."), **kwargs
            )
        return self.executor.stage_ok()

    def get_challenge(self, *args, error_message: str | None = None, **kwargs):
        return AccessDeniedChallenge(
            data={
                "component": "ak-stage-access-denied",
                "error_message": str(error_message or "Unknown error"),
            }
        )
