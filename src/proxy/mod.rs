use argh::FromArgs;
use axum::extract::Request;

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik proxy outpost.
#[argh(subcommand, name = "proxy")]
pub(crate) struct Cli {}

pub(crate) mod tls {
    use rustls::{server::ClientHello, sign::CertifiedKey};
    use std::sync::Arc;

    #[derive(Debug)]
    pub(crate) struct CertResolver {}

    impl CertResolver {
        pub(crate) fn resolve(&self, _client_hello: &ClientHello<'_>) -> Option<Arc<CertifiedKey>> {
            None
        }
    }
}

pub(crate) fn can_handle(_request: &Request) -> bool {
    false
}
