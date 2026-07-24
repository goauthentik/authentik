use std::{sync::Arc, time::Duration};

use ak_client::{
    apis::configuration::Configuration,
    models::{ProxyMode, ProxyOutpostConfig},
};
use ak_common::{config, tls::store::Certificate};
use arc_swap::ArcSwapOption;
use axum::{Router, routing::any};
use eyre::{Result, eyre};
use jsonwebtoken::jwk::JwkSet;
use moka::future::Cache;
use tracing::instrument;
use url::Url;

use crate::outpost::proxy::{
    ProxyOutpost, allowlist,
    claims::Claims,
    cookie::SessionCookie,
    endpoint::OidcEndpoint,
    session::{SessionStore, filesystem::FsSessionStore},
    upstream,
};

pub(crate) mod handlers;

#[derive(Debug)]
pub(super) struct Application {
    pub(super) host: String,
    pub(super) provider: ProxyOutpostConfig,
    pub(super) router: Router<Arc<Self>>,
    pub(super) cert: Option<Arc<Certificate>>,
    pub(super) endpoint: OidcEndpoint,
    pub(super) session_store: SessionStore,
    pub(super) session_cookie: SessionCookie,
    /// Authenticated API client configuration (backchannel calls + events API).
    pub(super) api_config: Configuration,
    /// `Host` header for backchannel token requests (browser host), if rewriting applies.
    pub(super) token_host: Option<String>,
    /// Short-lived cache of claims keyed by the `Authorization` header.
    pub(super) auth_cache: Cache<String, Claims>,
    /// Outpost name, sent upstream as `X-authentik-meta-outpost`.
    pub(super) outpost_name: String,
    /// Compiled `skip_path_regex` patterns for unauthenticated access.
    pub(super) unauthenticated_regex: Vec<regex::Regex>,
    /// Client used to forward requests upstream (proxy mode).
    pub(super) upstream_client: upstream::UpstreamClient,
    /// Cached provider JWKS for RS256 verification (refreshed on unknown `kid`).
    pub(super) jwks_cache: ArcSwapOption<JwkSet>,
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

        let embedded = outpost.controller.is_embedded();
        let authentik_host = outpost
            .controller
            .outpost
            .load()
            .config
            .get("authentik_host")
            .and_then(serde_json::Value::as_str)
            .and_then(|raw| Url::parse(raw).ok());
        let host_browser = config::get()
            .host_browser
            .as_deref()
            .filter(|raw| !raw.is_empty())
            .and_then(|raw| Url::parse(raw).ok());
        let endpoint = OidcEndpoint::new(
            &provider.oidc_configuration,
            authentik_host.as_ref(),
            host_browser.as_ref(),
            embedded,
        );
        let token_host = host_browser
            .as_ref()
            .or(authentik_host.as_ref())
            .map(|url| url.authority().to_owned());

        // Embedded outposts persist sessions in PostgreSQL; others use the filesystem.
        #[cfg(feature = "core")]
        let session_store = if embedded {
            SessionStore::Postgres(crate::outpost::proxy::session::postgres::PgSessionStore)
        } else {
            SessionStore::Filesystem(FsSessionStore::new(std::env::temp_dir())?)
        };
        #[cfg(not(feature = "core"))]
        let session_store = SessionStore::Filesystem(FsSessionStore::new(std::env::temp_dir())?);

        let unauthenticated_regex =
            allowlist::compile_skip_regex(provider.skip_path_regex.as_deref());

        let upstream_client =
            upstream::build_client(provider.internal_host_ssl_validation == Some(false))?;

        let session_cookie = SessionCookie::new(
            provider.client_id.as_deref().unwrap_or_default(),
            provider
                .cookie_secret
                .as_deref()
                .ok_or_else(|| eyre!("provider has no cookie secret"))?,
            external_url.scheme() == "https",
            provider.cookie_domain.clone(),
        )?;

        let router = Router::new()
            .route(
                "/outpost.goauthentik.io/start",
                any(handlers::handle_auth_start),
            )
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
                    "/outpost.goauthentik.io/auth/envoy/{*rest}",
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
            endpoint,
            session_store,
            session_cookie,
            api_config: outpost.controller.api_config.clone(),
            token_host,
            auth_cache: Cache::builder()
                .time_to_live(Duration::from_mins(1))
                .max_capacity(10_000)
                .build(),
            outpost_name: outpost.controller.outpost.load().name.clone(),
            unauthenticated_regex,
            upstream_client,
            jwks_cache: ArcSwapOption::empty(),
        })
    }

    /// Default session lifetime: the access token validity plus one second
    /// (so the session never outlives indefinitely), or zero if unset.
    pub(super) fn session_max_age(&self) -> Duration {
        self.provider
            .access_token_validity
            .map_or(Duration::ZERO, |validity| {
                Duration::from_secs_f64(validity + 1.0)
            })
    }
}
