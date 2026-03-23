use std::{sync::Arc, time::Duration};

use axum_server::tls_rustls::RustlsConfig;
use eyre::Result;
use rcgen::PKCS_ECDSA_P256_SHA256;
use rustls::{
    ServerConfig,
    server::{ClientHello, ResolvesServerCert, WebPkiClientVerifier},
    sign::CertifiedKey,
};
use tracing::{debug, warn};

use crate::{arbiter::Arbiter, brands, proxy};

pub(super) fn make_initial_tls_config() -> Result<RustlsConfig> {
    let (cert, keypair) = self_signed::generate(&PKCS_ECDSA_P256_SHA256)?;
    Ok(RustlsConfig::from_config(Arc::new(
        ServerConfig::builder()
            .with_no_client_auth()
            .with_single_cert(vec![cert.into()], keypair.into())?,
    )))
}

async fn make_tls_config(fallback: Arc<CertifiedKey>) -> Result<ServerConfig> {
    let (core_resolver, roots) = brands::tls::make_cert_managers().await?;
    let cert_resolver = CertResolver {
        core_resolver,
        proxy_resolver: None,
        fallback,
    };

    let client_cert_verifier = WebPkiClientVerifier::builder(Arc::new(roots))
        .allow_unauthenticated()
        .build()?;

    Ok(ServerConfig::builder()
        .with_client_cert_verifier(client_cert_verifier)
        .with_cert_resolver(Arc::new(cert_resolver)))
}

pub(super) async fn watch_tls_config(arbiter: Arbiter, config: RustlsConfig) -> Result<()> {
    tokio::select! {
        () = arbiter.gunicorn_ready() => {},
        () = arbiter.shutdown() => return Ok(()),
    }

    let fallback = Arc::new(self_signed::generate_certifiedkey(&PKCS_ECDSA_P256_SHA256)?);

    loop {
        match make_tls_config(Arc::clone(&fallback)).await {
            Ok(new_config) => {
                config.reload_from_config(Arc::new(new_config));
                debug!("reloaded tls config");
            }
            Err(err) => {
                warn!("error while reloading tls config {err:?}");
            }
        }

        tokio::select! {
            () = tokio::time::sleep(Duration::from_secs(60)) => {},
            () = arbiter.shutdown() => return Ok(()),
        }
    }
}

#[derive(Debug)]
struct CertResolver {
    core_resolver: brands::tls::CertResolver,
    proxy_resolver: Option<proxy::tls::CertResolver>,
    fallback: Arc<CertifiedKey>,
}

#[expect(
    clippy::missing_trait_methods,
    reason = "the provided methods are sensible enough"
)]
impl ResolvesServerCert for CertResolver {
    fn resolve(&self, client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if client_hello.server_name().is_none() {
            Some(Arc::clone(&self.fallback))
        } else if let Some(resolver) = &self.proxy_resolver
            && let Some(cert) = resolver.resolve(&client_hello)
        {
            Some(cert)
        } else if let Some(cert) = self.core_resolver.resolve(&client_hello) {
            Some(cert)
        } else {
            Some(Arc::clone(&self.fallback))
        }
    }
}

mod self_signed {
    use eyre::Result;
    use rcgen::{
        Certificate, CertificateParams, DistinguishedName, DnType, ExtendedKeyUsagePurpose,
        KeyPair, KeyUsagePurpose, SanType, SignatureAlgorithm,
    };
    use rustls::{
        crypto::aws_lc_rs::sign::any_supported_type,
        pki_types::{CertificateDer, PrivateKeyDer},
        sign::CertifiedKey,
    };
    use time::{Duration, OffsetDateTime};

    pub(super) fn generate(alg: &'static SignatureAlgorithm) -> Result<(Certificate, KeyPair)> {
        let signing_key = KeyPair::generate_for(alg)?;

        let mut params = CertificateParams::default();
        params.not_before = OffsetDateTime::now_utc();
        params.not_after = OffsetDateTime::now_utc() + Duration::days(365);
        params.distinguished_name = {
            let mut dn = DistinguishedName::new();
            dn.push(DnType::OrganizationName, "authentik");
            dn.push(DnType::CommonName, "authentik default certificate");
            dn
        };
        params.subject_alt_names = vec![SanType::DnsName("*".try_into()?)];
        params.key_usages = vec![
            KeyUsagePurpose::DigitalSignature,
            KeyUsagePurpose::KeyEncipherment,
        ];
        params.extended_key_usages = vec![ExtendedKeyUsagePurpose::ServerAuth];

        let cert = params.self_signed(&signing_key)?;

        Ok((cert, signing_key))
    }

    pub(super) fn generate_certifiedkey(alg: &'static SignatureAlgorithm) -> Result<CertifiedKey> {
        let (cert, keypair) = generate(alg)?;

        let cert_der = cert.der().to_vec();
        let key_der = keypair.serialize_der();

        let private_key =
            PrivateKeyDer::try_from(key_der).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;
        let signing_key =
            any_supported_type(&private_key).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;

        Ok(CertifiedKey::new(
            vec![CertificateDer::from(cert_der)],
            signing_key,
        ))
    }
}
