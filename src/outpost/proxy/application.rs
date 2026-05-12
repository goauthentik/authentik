use std::sync::Arc;

use ak_client::models::ProxyOutpostConfig;
use ak_common::tls::store::Certificate;
use axum::Router;
use eyre::{Result, eyre};
use tracing::instrument;
use url::Url;

use crate::outpost::proxy::ProxyOutpost;

const _REDIRECT_PARAM: &str = "rd";
const CALLBACK_SIGNATURE: &str = "X-authentik-auth-callback";
const _LOGOUT_SIGNATURE: &str = "X-authentik-logout";

#[derive(Debug)]
pub(super) struct Application {
    pub(super) host: String,
    pub(super) provider: ProxyOutpostConfig,
    pub(super) router: Router,
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

        let _redirect_url = {
            let mut redirect_url = external_url.join("outpost.goauthentik.io/callback")?;
            redirect_url.set_query(Some(&format!("{CALLBACK_SIGNATURE}=true")));
            redirect_url
        };

        let router = Router::new();

        Ok(Self {
            host: external_host.to_owned(),
            provider,
            router,
            cert,
        })
    }
}
