use ak_axum::extract::host::Host;
use axum::extract::State;
use axum::http::Method;
use metrics::histogram;
use std::sync::Arc;
use tokio::time::Instant;

use axum::http::StatusCode;
use axum::response::IntoResponse;

use crate::outpost::proxy::ProxyOutpost;

pub(super) async fn handle_ping(
    method: Method,
    Host(host): Host,
    State(outpost): State<Arc<ProxyOutpost>>,
) -> impl IntoResponse {
    let start = Instant::now();
    histogram!(
        "authentik_outpost_proxy_request_duration_seconds",
        "outpost_name" => outpost.controller.outpost.load().name.clone(),
        "method" => method.to_string(),
        "host" => host,
        "type" => "ping",
    )
    .record(start.elapsed().as_secs_f64());
    StatusCode::NO_CONTENT
}

pub(super) async fn default(State(_outpost): State<Arc<ProxyOutpost>>) -> impl IntoResponse {
    StatusCode::NOT_FOUND
}
