use std::{sync::Arc, time::Duration};

use ak_common::{Arbiter, Event, tls::self_signed};
use axum_server::tls_rustls::RustlsConfig;
use eyre::Result;
use rustls::{
    ServerConfig,
    server::{ClientHello, ResolvesServerCert, WebPkiClientVerifier},
    sign::CertifiedKey,
};
use tracing::{debug, info, warn};

use crate::{brands, outpost::proxy::ProxyOutpost};

pub(super) fn make_initial_tls_config() -> Result<RustlsConfig> {
    let (cert, keypair) = self_signed::generate()?;
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
    let mut events_rx = arbiter.events_subscribe();

    info!("waiting for gunicorn to be ready before starting tls watcher");
    loop {
        tokio::select! {
            event = events_rx.recv() => {
                if event == Ok(Event::GunicornIsReady) {
                    break;
                }
            },
            () = arbiter.shutdown() => {
                warn!("we were told to shutdown before starting the tls watcher");
                return Ok(());
            },
        }
    }
    info!("starting tls watcher");

    let fallback = Arc::new(self_signed::generate_certifiedkey()?);

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
    core_resolver: brands::tls::BrandCertResolver,
    proxy_resolver: Option<ProxyOutpost>,
    fallback: Arc<CertifiedKey>,
}

impl ResolvesServerCert for CertResolver {
    fn resolve(&self, client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if client_hello.server_name().is_none() {
            Some(Arc::clone(&self.fallback))
        } else if let Some(resolver) = &self.proxy_resolver
            && let Some(cert) = resolver.resolve_cert(&client_hello)
        {
            Some(cert)
        } else if let Some(cert) = self.core_resolver.resolve(&client_hello) {
            Some(cert)
        } else {
            Some(Arc::clone(&self.fallback))
        }
    }

    fn only_raw_public_keys(&self) -> bool {
        false
    }
}
