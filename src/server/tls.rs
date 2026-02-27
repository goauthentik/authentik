use std::{net::SocketAddr, sync::Arc, time::Duration};

use axum::Router;
use axum_server::{
    Handle,
    accept::DefaultAcceptor,
    tls_rustls::{RustlsAcceptor, RustlsConfig},
};
use eyre::Result;
use rcgen::PKCS_ECDSA_P256_SHA256;
use rustls::{
    ServerConfig,
    server::{ClientHello, ResolvesServerCert, WebPkiClientVerifier},
    sign::CertifiedKey,
};
use tracing::{debug, info, warn};

use crate::{
    arbiter::Arbiter,
    axum::accept::{proxy_protocol::ProxyProtocolAcceptor, tls::TlsAcceptor},
    proxy,
    server::core,
};

pub(super) async fn run_server_tls(
    router: Router,
    addr: SocketAddr,
    config: RustlsConfig,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    info!(addr = addr.to_string(), "starting tls server");
    axum_server::Server::bind(addr)
        .acceptor(TlsAcceptor::new(RustlsAcceptor::new(config).acceptor(
            ProxyProtocolAcceptor::new().acceptor(DefaultAcceptor::new()),
        )))
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}

pub(super) fn make_initial_tls_config() -> Result<RustlsConfig> {
    let (cert, keypair) = self_signed::generate(&PKCS_ECDSA_P256_SHA256)?;
    Ok(RustlsConfig::from_config(Arc::new(
        ServerConfig::builder()
            .with_no_client_auth()
            .with_single_cert(vec![cert.into()], keypair.into())?,
    )))
}

async fn make_tls_config(fallback: Arc<CertifiedKey>) -> Result<ServerConfig> {
    let (core_resolver, roots) = core::tls::make_cert_managers().await?;
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
        _ = arbiter.gunicorn_ready() => {},
        _ = arbiter.shutdown() => return Ok(()),
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
            _ = tokio::time::sleep(Duration::from_secs(60)) => {},
            _ = arbiter.shutdown() => return Ok(()),
        }
    }
}

#[derive(Debug)]
struct CertResolver {
    core_resolver: core::tls::CertResolver,
    proxy_resolver: Option<proxy::tls::CertResolver>,
    fallback: Arc<CertifiedKey>,
}

impl ResolvesServerCert for CertResolver {
    fn resolve(&self, client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if client_hello.server_name().is_none() {
            Some(self.fallback.clone())
        } else if let Some(resolver) = &self.proxy_resolver
            && let Some(cert) = resolver.resolve(&client_hello)
        {
            Some(cert)
        } else if let Some(cert) = self.core_resolver.resolve(&client_hello) {
            Some(cert)
        } else {
            Some(self.fallback.clone())
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

    pub(super) fn generate(alg: &'static SignatureAlgorithm) -> Result<(Certificate, KeyPair)> {
        let signing_key = KeyPair::generate_for(alg)?;

        let mut params: CertificateParams = Default::default();
        params.not_before = time::OffsetDateTime::now_utc();
        params.not_after = time::OffsetDateTime::now_utc() + time::Duration::days(365);
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
