use std::sync::Arc;

use ak_client::{
    apis::crypto_api::{
        crypto_certificatekeypairs_view_certificate_retrieve,
        crypto_certificatekeypairs_view_private_key_retrieve,
    },
    models::ProxyOutpostConfig,
};
use axum::Router;
use eyre::{Result, eyre};
use rustls::{
    crypto::CryptoProvider,
    pki_types::{CertificateDer, PrivateKeyDer, pem::PemObject as _},
    sign::CertifiedKey,
};
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
    pub(super) cert: Option<Arc<CertifiedKey>>,
}

impl Application {
    #[instrument(skip_all)]
    pub(super) async fn new(outpost: &ProxyOutpost, provider: ProxyOutpostConfig) -> Result<Self> {
        let external_url = Url::parse(&provider.external_host)?;
        if !external_url.has_authority() {
            return Err(eyre!("no host in external host"));
        }
        let external_host = external_url.authority();

        // TODO: extract this to a certificate store to avoid re-fetching the certificate every time
        let cert = if let Some(Some(kp_uuid)) = provider.certificate {
            let cert = crypto_certificatekeypairs_view_certificate_retrieve(
                &outpost.controller.api_config,
                &kp_uuid.to_string(),
                None,
            )
            .await?;
            let key = crypto_certificatekeypairs_view_private_key_retrieve(
                &outpost.controller.api_config,
                &kp_uuid.to_string(),
                None,
            )
            .await?;
            let cert_chain = CertificateDer::pem_reader_iter(cert.data.as_bytes())
                .collect::<Result<Vec<_>, _>>()?;
            let key_der = PrivateKeyDer::from_pem_reader(key.data.as_bytes())?;
            let provider = CryptoProvider::get_default().expect("no rustls provider installed");
            Some(Arc::new(CertifiedKey::new(
                cert_chain,
                provider.key_provider.load_private_key(key_der)?,
            )))
        } else {
            None
        };

        let _redirect_url = {
            let mut redirect_url = external_url.join("outpost.goauthentik.io/callback")?;
            redirect_url.set_query(Some(&format!("{CALLBACK_SIGNATURE}=true")));
            redirect_url
        };

        Ok(Self {
            host: external_host.to_owned(),
            provider,
            router: Router::new(),
            cert,
        })
    }
}
