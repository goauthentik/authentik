from urllib.parse import unquote

from cryptography.x509 import Certificate, load_pem_x509_certificate

from authentik.flows.stage import ChallengeStageView

HEADER_PROXY_FORWARDED = "HTTP_X_FORWARDED_CLIENT_CERT"
HEADER_NGINX_FORWARDED = "HTTP_SSL_CLIENT_CERT"


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
                cert = load_pem_x509_certificate(unquote(raw_cert["Cert"]))
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
            cert = load_pem_x509_certificate(unquote(sslcc_raw))
            return [cert]
        except ValueError:
            return []

    def dispatch(self, request, *args, **kwargs):
        certs = [
            *self._parse_cert_xfcc(),
            *self._parse_cert_nginx()
        ]
