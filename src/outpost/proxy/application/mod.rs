use std::sync::Arc;

use ak_client::models::{ProxyMode, ProxyOutpostConfig};
use ak_common::tls::store::Certificate;
use axum::{Router, routing::any};
use eyre::{Result, eyre};
use tracing::instrument;
use url::Url;

use crate::outpost::proxy::ProxyOutpost;

pub(super) mod handlers;

#[derive(Debug)]
pub(super) struct Application {
    pub(super) host: String,
    pub(super) provider: ProxyOutpostConfig,
    pub(super) router: Router<Arc<Self>>,
    pub(super) cert: Option<Arc<Certificate>>,
}

impl Application {
    #[instrument(skip_all)]
    pub(super) async fn new(outpost: &ProxyOutpost, provider: ProxyOutpostConfig) -> Result<Self> {
        let external_url = Url::parse(&provider.external_host)?;
        if !external_url.has_authority() {
            return Err(eyre!("no host in external host"));
        }
        let external_host = external_url.authority();

        let _old_app = outpost.apps.load().get(external_host);

        let cert = if let Some(Some(kp_uuid)) = provider.certificate {
            Some(
                outpost
                    .certificate_store
                    .ensure_keypair(&outpost.controller.api_config, kp_uuid)
                    .await?,
            )
        } else {
            None
        };

        let router = Router::new()
            // TODO: /start
            .route(
                "/outpost.goauthentik.io/callback",
                any(handlers::handle_auth_callback),
            )
            .route(
                "/outpost.goauthentik.io/sign_out",
                any(handlers::handle_sign_out),
            );

        let router = match provider.mode {
            Some(ProxyMode::ForwardSingle | ProxyMode::ForwardDomain) => router
                .route(
                    "/outpost.goauthentik.io/auth/caddy",
                    any(handlers::forward::handle_caddy),
                )
                .route(
                    "/outpost.goauthentik.io/auth/envoy",
                    any(handlers::forward::handle_envoy),
                )
                .route(
                    "/outpost.goauthentik.io/auth/nginx",
                    any(handlers::forward::handle_nginx),
                )
                .route(
                    "/outpost.goauthentik.io/auth/traefik",
                    any(handlers::forward::handle_traefik),
                ),
            Some(ProxyMode::Proxy) => router.fallback(handlers::proxy::handle),
            None => return Err(eyre!("no provider mode set")),
        };

        Ok(Self {
            host: external_host.to_owned(),
            provider,
            router,
            cert,
        })
    }
}
