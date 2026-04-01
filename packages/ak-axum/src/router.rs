//! Utilities for working with [`Router`].

use ak_common::config;
use axum::{Router, http::StatusCode};
use tower::ServiceBuilder;
use tower_http::timeout::TimeoutLayer;

/// Wrap a [`Router`] with common middlewares.
#[inline]
pub fn wrap_router(router: Router) -> Router {
    let config = config::get();
    let timeout = durstr::parse(&config.web.timeout_http_read_header)
        .expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_read).expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_write).expect("Invalid duration in http timeout")
        + durstr::parse(&config.web.timeout_http_idle).expect("Invalid duration in http timeout");
    let service_builder = ServiceBuilder::new().layer(TimeoutLayer::with_status_code(
        StatusCode::REQUEST_TIMEOUT,
        timeout,
    ));
    router.layer(service_builder)
}
