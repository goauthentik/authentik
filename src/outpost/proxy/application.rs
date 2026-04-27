use url::Url;

use ak_client::models::ProxyOutpostConfig;
use eyre::{Result, eyre};
use tracing::instrument;

use crate::outpost::proxy::ProxyOutpost;

const REDIRECT_PARAM: &str = "rd";
const CALLBACK_SIGNATURE: &str = "X-authentik-auth-callback";
const LOGOUT_SIGNATURE: &str = "X-authentik-logout";

pub(super) struct Application {
    pub(super) host: String,
}

impl Application {
    #[instrument(skip_all)]
    pub(super) fn new(
        _existing_apps: &ProxyOutpost,
        provider: &ProxyOutpostConfig,
    ) -> Result<Self> {
        let external_url = Url::parse(&provider.external_host)?;
        let external_host = external_url
            .host_str()
            .ok_or_else(|| eyre!("no host in external host"))?;

        let _redirect_url = {
            let mut redirect_url = external_url.join("outpost.goauthentik.io/callback")?;
            redirect_url.set_query(Some(&format!("{CALLBACK_SIGNATURE}=true")));
            redirect_url
        };

        Ok(Self {
            host: external_host.to_owned(),
        })
    }
}
