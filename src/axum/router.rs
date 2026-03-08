use axum::{Router, middleware::from_fn};
use tower::ServiceBuilder;

use crate::axum::{
    extract::{
        client_ip::client_ip_middleware, host::host_middleware, scheme::scheme_middleware,
        trusted_proxy::trusted_proxy_middleware,
    },
    trace::trace_layer,
};

#[inline]
pub(crate) fn wrap_router(router: Router, with_trace: bool) -> Router {
    let service_builder = ServiceBuilder::new()
        .layer(from_fn(trusted_proxy_middleware))
        .layer(from_fn(client_ip_middleware))
        .layer(from_fn(scheme_middleware))
        .layer(from_fn(host_middleware));
    if with_trace {
        router.layer(service_builder.layer(trace_layer()))
    } else {
        router.layer(service_builder)
    }
}
