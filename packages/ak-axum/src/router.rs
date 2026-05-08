//! Utilities for working with [`Router`].

use ak_common::config;
use axum::{
    Router,
    extract::Request,
    http::{HeaderName, HeaderValue, StatusCode},
    middleware::{Next, from_fn},
    response::Response,
};
use tower::ServiceBuilder;
use tower_http::timeout::TimeoutLayer;

use crate::{
    extract::{
        client_ip::client_ip_middleware, host::host_middleware, scheme::scheme_middleware,
        trusted_proxy::trusted_proxy_middleware,
    },
    tracing::{span_middleware, tracing_middleware},
};

const X_POWERED_BY: HeaderName = HeaderName::from_static("x-powered-by");

async fn powered_by_authentik_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;
    response
        .headers_mut()
        .insert(X_POWERED_BY, HeaderValue::from_static("authentik"));
    response
}

/// Wrap a [`Router`] with common middlewares.
///
/// Set `with_tracing` to [`true`] to log requests.
#[inline]
pub fn wrap_router(router: Router, with_tracing: bool) -> Router {
    let config = config::get();
    let timeout = durstr::parse(&config.web.timeout_http_read_header)
        .expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_read).expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_write).expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_idle).expect("Invalid duration in http timeout");
    let service_builder = ServiceBuilder::new()
        .layer(TimeoutLayer::with_status_code(
            StatusCode::REQUEST_TIMEOUT,
            timeout,
        ))
        .layer(from_fn(span_middleware))
        .layer(from_fn(powered_by_authentik_middleware))
        .layer(from_fn(trusted_proxy_middleware))
        .layer(from_fn(client_ip_middleware))
        .layer(from_fn(scheme_middleware))
        .layer(from_fn(host_middleware));
    if with_tracing {
        router.layer(service_builder.layer(from_fn(tracing_middleware)))
    } else {
        router.layer(service_builder)
    }
}
