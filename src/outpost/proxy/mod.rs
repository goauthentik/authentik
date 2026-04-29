use std::{collections::HashMap, sync::Arc};

use ak_axum::router::wrap_router;
use ak_client::{apis::outposts_api::outposts_proxy_list, models::ProxyMode};
use ak_common::{Tasks, api::fetch_all, config};
use arc_swap::ArcSwap;
use argh::FromArgs;
use axum::Router;
use eyre::Result;
use tracing::{debug, error, info, instrument, warn};

use crate::outpost::{Outpost, OutpostController, proxy::application::Application};

mod application;
mod handlers;

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik proxy outpost.
#[argh(subcommand, name = "proxy")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

pub(crate) struct ProxyOutpost {
    controller: Arc<OutpostController>,
    apps: ArcSwap<HashMap<String, Arc<Application>>>,
}

impl Outpost for ProxyOutpost {
    type Cli = Cli;

    const OUTPOST_TYPE: &'static str = "proxy";

    #[instrument(skip_all)]
    async fn new(controller: Arc<OutpostController>) -> Result<Self> {
        Ok(Self {
            controller,
            apps: ArcSwap::from_pointee(HashMap::with_capacity(0)),
        })
    }

    fn start(self: Arc<Self>, tasks: &mut Tasks) -> Result<()> {
        let router = build_router(self);

        for addr in config::get().listen.http.iter().copied() {
            ak_axum::server::start_plain(tasks, "proxy-outpost", router.clone(), addr, false)?;
        }

        Ok(())
    }

    #[instrument(skip_all)]
    async fn refresh(&self) -> Result<()> {
        debug!(
            outpost_pk = %self.controller.outpost.load().pk,
            "requesting providers for outpost"
        );

        let providers = fetch_all(
            |page| {
                outposts_proxy_list(
                    &self.controller.api_config,
                    None,
                    None,
                    Some(page),
                    Some(100_i32),
                    None,
                )
            },
            |r| &r.pagination,
            |r| r.results,
        )
        .await
        .inspect_err(|err| error!(?err, "failed to fetch providers"))?;
        debug!(count = providers.len(), "fetched providers");

        if providers.is_empty() && !self.controller.is_embedded() {
            warn!(
                "no providers assigned to this outpost, check outpost configuration in authentik"
            );
        }

        for (i, provider) in providers.iter().enumerate() {
            debug!(
                index = i,
                name = provider.name,
                external_host = provider.external_host,
                assigned_to_app = provider.assigned_application_name,
                "provider details"
            );
        }

        let mut apps = HashMap::with_capacity(providers.len());

        for provider in providers {
            let name = provider.name.clone();
            let Ok(application) = Application::new(self, provider)
                .inspect_err(|err| warn!(?err, "failed to setup application, skipping provider"))
            else {
                continue;
            };
            info!(name, host = application.host, "loaded application");

            apps.insert(application.host.clone(), Arc::new(application));
        }

        self.apps.store(Arc::new(apps));

        Ok(())
    }

    async fn end_session(&self, _event: super::event::EventSessionEnd) -> Result<()> {
        // todo!()
        warn!(?_event, "removing session");
        Ok(())
    }
}

impl ProxyOutpost {
    #[instrument(skip(self))]
    fn lookup_app(&self, host: &str) -> Option<Arc<Application>> {
        let apps = self.apps.load();

        // If we only have a single app, host name switching doesn't matter.
        if apps.len() == 1
            && let Some(app) = apps.values().next()
        {
            debug!(app = app.provider.name, "found a single app, using it");
            return Some(Arc::clone(app));
        }

        if let Some(app) = apps.get(host) {
            debug!(app = app.provider.name, "found app based direct host match");
            return Some(Arc::clone(app));
        }

        // For forward_auth_domain, we don't have a direct app to domain relationship.
        // Check through all apps, and check how much of their cookie domain matches the host.
        // Return the application that has the longest match.
        let mut longest_match = None;
        let mut longest_len = 0_usize;

        for app in apps.values() {
            if app.provider.mode != Some(ProxyMode::ForwardDomain) {
                continue;
            }

            if let Some(cookie_domain) = app.provider.cookie_domain.as_deref() {
                // Check if the cookie domain has a leading period for a wildcard.
                // This will decrease the weight of a wildcard domain, but a request to example.com
                // with the cookie domain set to example.com will still be routed correctly.
                let domain = cookie_domain.trim_start_matches('.');

                if host.ends_with(domain) && domain.len() > longest_len {
                    longest_len = domain.len();
                    longest_match = Some(Arc::clone(app));
                }
                // For forward_auth_domain, we need to response on the external domain too.
                if app.provider.external_host == host {
                    debug!(app = app.provider.name, "found app based on external_host");
                    return Some(Arc::clone(app));
                }
            }
        }

        if let Some(app) = &longest_match {
            debug!(app = app.provider.name, "found app based on cookie domain");
        }

        longest_match
    }
}

fn build_router(outpost: Arc<ProxyOutpost>) -> Router {
    wrap_router(
        Router::new()
            .nest(
                "/outpost.goauthentik.io/ping",
                Router::new().fallback(handlers::handle_ping),
            )
            .fallback(handlers::default)
            .with_state(outpost),
        true,
    )
}
