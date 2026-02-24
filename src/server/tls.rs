use std::{net::SocketAddr, sync::Arc};

use arc_swap::ArcSwapOption;
use axum::Router;
use axum_server::{
    Handle,
    accept::DefaultAcceptor,
    tls_rustls::{RustlsAcceptor, RustlsConfig},
};
use eyre::Result;
use rustls::{
    ServerConfig,
    server::{ClientHello, ResolvesServerCert},
    sign::CertifiedKey,
};
use tracing::info;

use crate::{
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

#[derive(Debug)]
struct CertResolver {
    core_manager: Arc<core::tls::CertificateManager>,
    proxy_resolver: Arc<ArcSwapOption<proxy::CertificateManager>>,
    fallback_resolver: fallback::CertResolver,
}

impl ResolvesServerCert for CertResolver {
    fn resolve(&self, client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if client_hello.server_name().is_none() {
            self.fallback_resolver.resolve(&client_hello)
        } else if let Some(resolver) = self.proxy_resolver.load().as_deref()
            && let Some(cert) = resolver.resolve(&client_hello)
        {
            Some(cert)
        } else if let Some(cert) = self.core_manager.resolve(&client_hello) {
            Some(cert)
        } else {
            self.fallback_resolver.resolve(&client_hello)
        }
    }
}

pub(super) fn make_tls_config(
    core_manager: Arc<core::tls::CertificateManager>,
    proxy_resolver: Arc<ArcSwapOption<proxy::CertificateManager>>,
) -> Result<ServerConfig> {
    let fallback_resolver = fallback::CertResolver::new()?;
    let resolver = CertResolver {
        core_manager,
        proxy_resolver,
        fallback_resolver,
    };
    let config = ServerConfig::builder()
        .with_no_client_auth()
        .with_cert_resolver(Arc::new(resolver));
    Ok(config)
}

mod fallback {
    use std::sync::Arc;

    use eyre::Result;
    use rcgen::{
        Certificate, CertificateParams, DistinguishedName, DnType, ExtendedKeyUsagePurpose,
        KeyPair, KeyUsagePurpose, PKCS_ECDSA_P256_SHA256, SanType, SignatureAlgorithm,
    };
    use rustls::{
        crypto::aws_lc_rs::sign::any_supported_type,
        pki_types::{CertificateDer, PrivateKeyDer},
        server::ClientHello,
        sign::CertifiedKey,
    };

    fn generate_self_signed_cert(
        alg: &'static SignatureAlgorithm,
    ) -> Result<(Certificate, KeyPair)> {
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

    #[derive(Debug)]
    pub(super) struct CertResolver {
        fallback: Arc<CertifiedKey>,
    }

    impl CertResolver {
        pub(super) fn new() -> Result<Self> {
            let (cert, keypair) = generate_self_signed_cert(&PKCS_ECDSA_P256_SHA256)?;

            let cert_der = cert.der().to_vec();
            let key_der = keypair.serialize_der();

            let private_key =
                PrivateKeyDer::try_from(key_der).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;
            let signing_key =
                any_supported_type(&private_key).map_err(|_| rcgen::Error::CouldNotParseKeyPair)?;

            Ok(Self {
                fallback: Arc::new(CertifiedKey::new(
                    vec![CertificateDer::from(cert_der)],
                    signing_key,
                )),
            })
        }

        pub(super) fn resolve(&self, _client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
            Some(Arc::clone(&self.fallback))
        }
    }
}
