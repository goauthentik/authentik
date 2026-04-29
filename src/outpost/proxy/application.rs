use ak_client::models::ProxyOutpostConfig;
use axum::Router;
use eyre::{Result, eyre};
use tracing::instrument;
use url::Url;

use crate::outpost::proxy::ProxyOutpost;

const REDIRECT_PARAM: &str = "rd";
const CALLBACK_SIGNATURE: &str = "X-authentik-auth-callback";
const LOGOUT_SIGNATURE: &str = "X-authentik-logout";

#[derive(Debug)]
pub(super) struct Application {
    pub(super) host: String,
    pub(super) provider: ProxyOutpostConfig,
    pub(super) router: Router,
}

impl Application {
    #[instrument(skip_all)]
    pub(super) fn new(_existing_apps: &ProxyOutpost, provider: ProxyOutpostConfig) -> Result<Self> {
        let external_url = Url::parse(&provider.external_host)?;
        if !external_url.has_authority() {
            return Err(eyre!("no host in external host"));
        }
        let external_host = external_url.authority();

        let _redirect_url = {
            let mut redirect_url = external_url.join("outpost.goauthentik.io/callback")?;
            redirect_url.set_query(Some(&format!("{CALLBACK_SIGNATURE}=true")));
            redirect_url
        };

        Ok(Self {
            host: external_host.to_owned(),
            provider,
            router: Router::new(),
        })
    }
}
