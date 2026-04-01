//! TLS utilities
use std::sync::Arc;

use eyre::{Result, eyre};
use rustls::server::ResolvesServerCert;

use crate::config;

/// Dummy resolver for FIPS compliance check.
#[derive(Debug)]
struct EmptyCertResolver;

#[expect(
    clippy::missing_trait_methods,
    reason = "this is just a dummy implementation to check FIPS compliance"
)]
impl ResolvesServerCert for EmptyCertResolver {
    fn resolve(
        &self,
        _client_hello: rustls::server::ClientHello<'_>,
    ) -> Option<Arc<rustls::sign::CertifiedKey>> {
        None
    }
}

/// Check if fips is enabled.
fn is_fips_enabled() -> bool {
    rustls::client::ClientConfig::builder()
        .with_root_certificates(rustls::RootCertStore::empty())
        .with_no_client_auth()
        .fips()
        && rustls::server::ServerConfig::builder()
            .with_no_client_auth()
            .with_cert_resolver(Arc::new(EmptyCertResolver {}))
            .fips()
}

/// Initialize default [`rustls`] crypto provider, and check that FIPS is working correctly.
pub fn init() -> Result<()> {
    #[expect(
        clippy::unwrap_in_result,
        reason = "result type does not implement Error"
    )]
    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .expect("Failed to install rustls provider");

    if config::get().compliance.fips.enabled && !is_fips_enabled() {
        return Err(eyre!("A non fips crypto provider was installed"));
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    #[test]
    fn init() {
        crate::config::init().expect("failed to initialize config");

        super::init().expect("failed to initialized rustls");
        assert!(super::is_fips_enabled());
    }
}
