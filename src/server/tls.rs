use std::{sync::Arc, time::Duration};

use ak_common::{Arbiter, Event};
use axum_server::tls_rustls::RustlsConfig;
use eyre::Result;
use rustls::{
    ServerConfig,
    server::{ClientHello, ResolvesServerCert, WebPkiClientVerifier},
    sign::CertifiedKey,
};
use tracing::{debug, info, warn};

use crate::{brands, server::Server};

pub(super) fn make_initial_tls_config(server: Arc<Server>) -> RustlsConfig {
    RustlsConfig::from_config(Arc::new(
        ServerConfig::builder()
            .with_no_client_auth()
            .with_cert_resolver(server),
    ))
}

impl ResolvesServerCert for Server {
    fn resolve(&self, client_hello: ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if client_hello.server_name().is_none() {
            Some(Arc::clone(&self.fallback_cert))
        } else if let Some(proxy_outpost) = self.proxy_outpost.load_full()
            && let Some(cert) = proxy_outpost.resolve_cert(&client_hello)
        {
            Some(cert)
        } else if let Some(cert) = self.resolve_cert(&client_hello) {
            Some(cert)
        } else {
            Some(Arc::clone(&self.fallback_cert))
        }
    }

    fn only_raw_public_keys(&self) -> bool {
        false
    }
}

impl Server {
    fn resolve_cert(&self, client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        if let Some(brand_cert_resolver) = self.brand_cert_resolver.load_full() {
            brand_cert_resolver.resolve(client_hello)
        } else {
            None
        }
    }
}

async fn update_tls_config(config: &RustlsConfig, server: &Arc<Server>) -> Result<()> {
    let (brand_core_resolver, roots) = brands::tls::make_cert_managers().await?;

    server
        .brand_cert_resolver
        .store(Some(Arc::new(brand_core_resolver)));

    let server_config = if roots.is_empty() {
        ServerConfig::builder().with_no_client_auth()
    } else {
        let client_cert_verifier = WebPkiClientVerifier::builder(Arc::new(roots))
            .allow_unauthenticated()
            .build()?;
        ServerConfig::builder().with_client_cert_verifier(client_cert_verifier)
    };
    let resolver: Arc<dyn ResolvesServerCert> = Arc::<Server>::clone(server);
    let server_config = server_config.with_cert_resolver(resolver);

    config.reload_from_config(Arc::new(server_config));

    Ok(())
}

pub(super) async fn watch_tls_config(
    arbiter: Arbiter,
    config: RustlsConfig,
    server: Arc<Server>,
) -> Result<()> {
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
    loop {
        if let Err(err) = update_tls_config(&config, &server).await {
            warn!(?err, "error while reloading tls config");
        } else {
            debug!("reloaded tls config");
        }

        tokio::select! {
            () = tokio::time::sleep(Duration::from_mins(1)) => {},
            () = arbiter.shutdown() => return Ok(()),
        }
    }
}
