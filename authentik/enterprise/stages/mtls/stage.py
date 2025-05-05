from urllib.parse import unquote

from cryptography.exceptions import InvalidSignature
from cryptography.x509 import Certificate, NameOID, ObjectIdentifier, load_pem_x509_certificate
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
from authentik.stages.password.stage import PLAN_CONTEXT_METHOD, PLAN_CONTEXT_METHOD_ARGS
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT

# All of these headers must only be accepted from "trusted" reverse proxies
# See internal/web/proxy.go:39
HEADER_PROXY_FORWARDED = "X-Forwarded-Client-Cert"
HEADER_NGINX_FORWARDED = "SSL-Client-Cert"
HEADER_TRAEFIK_FORWARDED = "X-Forwarded-TLS-Client-Cert"


class MTLSStageView(ChallengeStageView):

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
            try:
                cert = load_pem_x509_certificate(unquote(raw_cert["Cert"]).encode())
                certs.append(cert)
            except ValueError:
                continue
        return certs

    def _parse_cert_nginx(self) -> list[Certificate]:
        """Parse certificates in the format nginx-ingress gives to us"""
        sslcc_raw = self.request.headers.get(HEADER_NGINX_FORWARDED)
        if not sslcc_raw:
            return []
        try:
            cert = load_pem_x509_certificate(unquote(sslcc_raw).encode())
            return [cert]
        except ValueError:
            return []

    def _parse_cert_traefik(self) -> list[Certificate]:
        """Parse certificates in the format traefik gives to us"""
        ftcc_raw = self.request.headers.get(HEADER_TRAEFIK_FORWARDED)
        if not ftcc_raw:
            return []
        try:
            cert = load_pem_x509_certificate(unquote(ftcc_raw).encode())
            return [cert]
        except ValueError:
            return []

    def get_ca(self) -> CertificateKeyPair | None:
        # We can't access `certificate_authority` on `self.executor.current_stage`, as that would
        # load the certificate into the directly referenced foreign key, which we have to pickle
        # as part of the flow plan, and cryptography certs can't be pickled
        stage: MutualTLSStage = (
            MutualTLSStage.objects.filter(pk=self.executor.current_stage.pk)
            .select_related("certificate_authority")
            .first()
        )
        if stage.certificate_authority:
            return stage.certificate_authority
        brand: Brand = self.request.brand
        if brand.client_certificate:
            return brand.client_certificate
        return None

    def validate_cert(self, ca: Certificate, certs: list[Certificate]):
        for _cert in certs:
            try:
                _cert.verify_directly_issued_by(ca)
                return _cert
            except (InvalidSignature, TypeError, ValueError):
                continue

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

    def auth_user(self, user: User, cert: Certificate):
        self.executor.plan.context[PLAN_CONTEXT_PENDING_USER] = user
        self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD, "mtls")
        self.executor.plan.context.setdefault(PLAN_CONTEXT_METHOD_ARGS, {})
        self.executor.plan.context[PLAN_CONTEXT_METHOD_ARGS].update(
            {
                "certificate": {
                    "serial_number": cert.serial_number,
                    "subject": cert.subject.rfc4514_string(),
                    # TODO: Other attributes
                }
            }
        )

    def enroll_prepare_user(self, cert: Certificate):
        self.executor.plan.context.setdefault(PLAN_CONTEXT_PROMPT, {})
        self.executor.plan.context[PLAN_CONTEXT_PROMPT].update(
            {
                "email": self.get_cert_attribute(cert, NameOID.EMAIL_ADDRESS),
                "name": self.get_cert_attribute(cert, NameOID.COMMON_NAME),
            }
        )

    def get_cert_attribute(self, cert: Certificate, oid: ObjectIdentifier) -> str | None:
        attr = cert.subject.get_attributes_for_oid(oid)
        if len(attr) < 1:
            return None
        return str(attr[0].value)

    def dispatch(self, request, *args, **kwargs):
        stage: MutualTLSStage = self.executor.current_stage
        certs = [*self._parse_cert_xfcc(), *self._parse_cert_nginx(), *self._parse_cert_traefik()]
        ca = self.get_ca()
        if not ca and stage.mode != TLSMode.OPTIONAL:
            self.logger.warning("No Certificate authority found")
            return super().dispatch(request, *args, **kwargs)
        cert = self.validate_cert(ca.certificate, certs)
        if len(certs) < 1 and stage.mode == TLSMode.REQUIRED:
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
        if existing_user and self.executor.flow.designation == FlowDesignation.AUTHENTICATION:
            self.auth_user(existing_user, cert)
        elif not existing_user and self.executor.flow.designation == FlowDesignation.ENROLLMENT:
            self.enroll_prepare_user(cert)
        else:
            self.logger.warning("Invalid configuration")
            return super().dispatch(request, *args, **kwargs)
        return self.executor.stage_ok()

    def get_challenge(self, *args, error_message: str | None = None, **kwargs):
        return AccessDeniedChallenge(
            data={
                "component": "ak-stage-access-denied",
                "error_message": str(error_message or "Unknown error"),
            }
        )
