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
    // HTTP/1.1 only. The Go outpost this replaced used a bare
    // `http.Transport{TLSClientConfig: ..}` and never set `ForceAttemptHTTP2`,
    // which per net/http "conservatively disables HTTP/2", so upstreams were
    // only ever spoken to over HTTP/1.1.
    //
    // Negotiating h2 here breaks two things at once. The inbound `Host` this
    // proxy forwards (see `set_host(false)` below) sits alongside the
    // `:authority` hyper derives from the upstream URI; when they differ that
    // is malformed (RFC 9113 8.3.1) and compliant upstreams answer 400. And
    // `Upgrade`/`Connection` are forbidden in HTTP/2 (8.2.2), so hyper strips
    // them and every WebSocket silently degrades into an ordinary request --
    // HTTP/2 has no 101 either (8.6).
    //
    // Speaking h2 upstream *correctly* would mean decoupling `:authority` from
    // the dial target, which `hyper_util::client::legacy` cannot do: its pool
    // key is `(scheme, authority)` and the connector dials that same tuple.
    .enable_http1()
    .build();
    // Forward the request's own `Host` upstream instead of deriving it from the
    // (internal) upstream URI authority. The proxy sets `Host` explicitly.
    Ok(Client::builder(TokioExecutor::new())
        .set_host(false)
        .http1_title_case_headers(true)
        .build(connector))
}
