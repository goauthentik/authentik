use std::sync::Arc;

use argh::FromArgs;
use axum::extract::Request;
use rustls::{server::ClientHello, sign::CertifiedKey};

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik proxy outpost.
#[argh(subcommand, name = "proxy")]
pub(crate) struct Cli {}

#[derive(Debug)]
pub(crate) struct CertificateManager {}

impl CertificateManager {
    pub(crate) fn resolve(&self, _client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
        None
    }
}

pub(crate) fn can_handle(_request: &Request) -> bool {
    false
}
