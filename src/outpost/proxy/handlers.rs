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
use tower::util::ServiceExt as _;
use tracing::{Instrument as _, field, info_span, instrument, trace, warn};

use crate::outpost::proxy::ProxyOutpost;

#[instrument(skip_all)]
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

#[instrument(skip_all)]
pub(super) async fn default(
    method: Method,
    Host(host): Host,
    State(outpost): State<Arc<ProxyOutpost>>,
    request: Request,
) -> Result<Response> {
    let span = info_span!("proxy outpost request", user = field::Empty);
    let start = Instant::now();

    let Some(app) = outpost.lookup_app(&host) else {
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
    let response = app.router.clone().oneshot(request).instrument(span).await?;

    histogram!(
        "authentik_outpost_proxy_request_duration_seconds",
        "outpost_name" => outpost.controller.outpost.load().name.clone(),
        "method" => method.to_string(),
        "host" => host,
        "type" => "app",
    )
    .record(start.elapsed().as_secs_f64());

    Ok(response)
}
