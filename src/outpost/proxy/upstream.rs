//! HTTP client used to forward requests to upstream application servers.

use std::sync::Arc;

use axum::body::Body;
use eyre::Result;
use hyper_rustls::{HttpsConnector, HttpsConnectorBuilder};
use hyper_util::{
    client::legacy::{Client, connect::HttpConnector},
    rt::TokioExecutor,
};
use rustls::{
    ClientConfig, DigitallySignedStruct, Error as RustlsError, SignatureScheme,
    client::danger::{HandshakeSignatureValid, ServerCertVerified, ServerCertVerifier},
    pki_types::{CertificateDer, ServerName, UnixTime},
};

/// Client forwarding to upstream servers (HTTP or HTTPS, with optional upgrades).
pub(super) type UpstreamClient = Client<HttpsConnector<HttpConnector>, Body>;

/// Build the upstream client. When `insecure`, upstream TLS certificates are
/// not validated (mirrors `internal_host_ssl_validation = false`).
pub(super) fn build_client(insecure: bool) -> Result<UpstreamClient> {
    let builder = HttpsConnectorBuilder::new();
    let connector = if insecure {
        builder.with_tls_config(insecure_tls_config())
    } else {
        builder.with_native_roots()?
    }
    .https_or_http()
    .enable_http1()
    .enable_http2()
    .build();
    // Forward the request's own `Host` upstream instead of deriving it from the
    // (internal) upstream URI authority. The proxy sets `Host` explicitly.
    Ok(Client::builder(TokioExecutor::new())
        .set_host(false)
        .build(connector))
}

fn insecure_tls_config() -> ClientConfig {
    ClientConfig::builder()
        .dangerous()
        .with_custom_certificate_verifier(Arc::new(NoCertificateVerification))
        .with_no_client_auth()
}

/// Certificate verifier that accepts any upstream certificate.
#[derive(Debug)]
struct NoCertificateVerification;

#[expect(
    clippy::missing_trait_methods,
    reason = "the trait's defaulted methods are appropriate for an accept-all verifier"
)]
impl ServerCertVerifier for NoCertificateVerification {
    fn verify_server_cert(
        &self,
        _end_entity: &CertificateDer<'_>,
        _intermediates: &[CertificateDer<'_>],
        _server_name: &ServerName<'_>,
        _ocsp_response: &[u8],
        _now: UnixTime,
    ) -> Result<ServerCertVerified, RustlsError> {
        Ok(ServerCertVerified::assertion())
    }

    fn verify_tls12_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, RustlsError> {
        Ok(HandshakeSignatureValid::assertion())
    }

    fn verify_tls13_signature(
        &self,
        _message: &[u8],
        _cert: &CertificateDer<'_>,
        _dss: &DigitallySignedStruct,
    ) -> Result<HandshakeSignatureValid, RustlsError> {
        Ok(HandshakeSignatureValid::assertion())
    }

    fn supported_verify_schemes(&self) -> Vec<SignatureScheme> {
        rustls::crypto::aws_lc_rs::default_provider()
            .signature_verification_algorithms
            .supported_schemes()
    }
}
