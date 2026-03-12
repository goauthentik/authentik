use axum::{Router, http::status::StatusCode, middleware::from_fn};
use tower::ServiceBuilder;
use tower_http::timeout::TimeoutLayer;

use crate::{
    axum::{
        extract::{
            client_ip::client_ip_middleware, host::host_middleware, scheme::scheme_middleware,
            trusted_proxy::trusted_proxy_middleware,
        },
        trace::{span_middleware, tracing_middleware},
    },
    config,
};

#[inline]
pub(crate) fn wrap_router(router: Router, with_trace: bool) -> Router {
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
        .layer(from_fn(trusted_proxy_middleware))
        .layer(from_fn(client_ip_middleware))
        .layer(from_fn(scheme_middleware))
        .layer(from_fn(host_middleware));
    if with_trace {
        router.layer(service_builder.layer(from_fn(tracing_middleware)))
    } else {
        router.layer(service_builder)
    }
}
