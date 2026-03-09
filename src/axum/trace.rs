use axum::{RequestPartsExt, extract::Request, middleware::Next, response::Response};
use tokio::time::Instant;
use tracing::{field, info, info_span, trace};

use crate::axum::extract::{client_ip::ClientIp, host::Host, scheme::Scheme};

pub(crate) async fn span_middleware(request: Request, next: Next) -> Response {
    let span = info_span!(
        "request",
        event = %request.uri(),
        method = %request.method(),
        remote = field::Empty,
        scheme = field::Empty,
        host = field::Empty,
    );
    let enter = span.enter();
    let response = next.run(request).await;
    drop(enter);
    response
}

pub(crate) async fn tracing_middleware(request: Request, next: Next) -> Response {
    let event = request.uri().clone();
    let method = request.method().clone();

    let (mut parts, body) = request.into_parts();
    let remote = parts
        .extract::<ClientIp>()
        .await
        .expect("No ClientIp found. Did you add the middleware?")
        .0;
    let scheme = parts
        .extract::<Scheme>()
        .await
        .expect("No Scheme found. Did you add the middleware?")
        .0;
    let host = parts
        .extract::<Host>()
        .await
        .expect("No Scheme found. Did you add the middleware?")
        .0;

    trace!(
        event = %event,
        method = %method,
        remote = %remote,
        scheme = %scheme,
        host = %host,
        "request"
    );

    let request = Request::from_parts(parts, body);

    let start = Instant::now();
    let response = next.run(request).await;
    let runtime = start.elapsed();
    let status = response.status().as_u16();

    info!(
        event = %event,
        method = %method,
        remote = %remote,
        scheme = %scheme,
        host = %host,
        status = status,
        runtime = runtime.as_millis(),
        "response"
    );

    response
}
