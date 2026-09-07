//! HTTP client used to forward requests to upstream application servers.

use ak_common::tls;
use axum::body::Body;
use eyre::Result;
use hyper_rustls::{HttpsConnector, HttpsConnectorBuilder};
use hyper_util::{
    client::legacy::{Client, connect::HttpConnector},
    rt::TokioExecutor,
};

/// Client forwarding to upstream servers (HTTP or HTTPS, with optional upgrades).
pub(super) type UpstreamClient = Client<HttpsConnector<HttpConnector>, Body>;

/// Build the upstream client. When `insecure`, upstream TLS certificates are
/// not validated (mirrors `internal_host_ssl_validation = false`).
pub(super) fn build_client(insecure: bool) -> Result<UpstreamClient> {
    let builder = HttpsConnectorBuilder::new();
    let connector = if insecure {
        builder.with_tls_config(tls::client::insecure_config())
    } else {
        builder.with_native_roots()?
    }
    .https_or_http()
    .enable_all_versions()
    .build();
    // Forward the request's own `Host` upstream instead of deriving it from the
    // (internal) upstream URI authority. The proxy sets `Host` explicitly.
    Ok(Client::builder(TokioExecutor::new())
        .set_host(false)
        .http1_title_case_headers(true)
        .build(connector))
}
