use std::sync::Arc;

use ak_axum::{error::Result, extract::host::Host};
use axum::{
    extract::{Request, State},
    http::{Method, StatusCode, header::CONTENT_TYPE},
    response::{IntoResponse as _, Response},
};
use metrics::histogram;
use serde_json::json;
use tokio::time::Instant;
use tracing::{instrument, trace, warn};

use crate::outpost::proxy::ProxyOutpost;

pub(super) async fn handle_ping(
    method: Method,
    Host(host): Host,
    State(outpost): State<Arc<ProxyOutpost>>,
) -> Response {
    let start = Instant::now();
    histogram!(
        "authentik_outpost_proxy_request_duration_seconds",
        "outpost_name" => outpost.controller.outpost.load().name.clone(),
        "method" => method.to_string(),
        "host" => host,
        "type" => "ping",
    )
    .record(start.elapsed().as_secs_f64());
    StatusCode::NO_CONTENT.into_response()
}

#[instrument(skip(request, outpost))]
pub(super) async fn default(
    Host(host): Host,
    State(outpost): State<Arc<ProxyOutpost>>,
    request: Request,
) -> Result<Response> {
    let Some(_app) = outpost.lookup_app(&host) else {
        trace!(headers = ?request.headers(), "tracing headers for no hostname match");
        warn!("no app for hostname");
        return Ok(Response::builder()
            .status(StatusCode::BAD_REQUEST)
            .header(CONTENT_TYPE, "application/json")
            .body(
                json!({
                    "message": "no app for hostname",
                    "host": host,
                    "detail": format!("check the outpost settings and make sure '{host}' is included."),
                })
                .to_string()
                .into(),
            )
            .expect("infallible"));
    };
    trace!("passing to application");

    Ok(StatusCode::NOT_FOUND.into_response())
}
