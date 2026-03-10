use std::collections::HashMap;

use axum::{extract::Request, middleware::Next, response::Response};
use tokio::time::Instant;
use tracing::{field, info, info_span, trace};

use crate::config;

pub(crate) async fn span_middleware(request: Request, next: Next) -> Response {
    let config = config::get();
    let http_headers = request
        .headers()
        .iter()
        .filter(|(name, _)| {
            for header in config.log.http_headers.iter() {
                if header.eq_ignore_ascii_case(name.as_str()) {
                    return true;
                }
            }
            false
        })
        .map(|(name, value)| (name.to_string().to_lowercase().replace("-", "_"), value))
        .collect::<HashMap<_, _>>();
    let span = info_span!(
        "request",
        path = %request.uri(),
        method = %request.method(),
        remote = field::Empty,
        scheme = field::Empty,
        host = field::Empty,
        http_headers = ?http_headers,
    );
    let _enter = span.enter();
    next.run(request).await
}

pub(crate) async fn tracing_middleware(request: Request, next: Next) -> Response {
    let event = request.uri().clone();
    trace!("request start");

    let start = Instant::now();
    let response = next.run(request).await;
    let runtime = start.elapsed();
    let status = response.status().as_u16();

    info!(status = status, runtime = runtime.as_millis(), "{event}");

    response
}
