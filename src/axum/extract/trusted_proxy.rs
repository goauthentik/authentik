use std::net::SocketAddr;

use axum::{
    Extension, RequestPartsExt,
    extract::{ConnectInfo, FromRequestParts, Request},
    http::request::Parts,
    middleware::Next,
    response::Response,
};
use tracing::{instrument, trace};

use crate::config;

#[derive(Clone, Copy, Debug)]
pub(crate) struct TrustedProxy(pub bool);

impl<S> FromRequestParts<S> for TrustedProxy
where S: Send + Sync
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(trusted_proxy)| trusted_proxy)
    }
}

#[instrument(skip_all)]
async fn extract_trusted_proxy(parts: &mut Parts) -> bool {
    if let Ok(ConnectInfo(addr)) = parts.extract::<ConnectInfo<SocketAddr>>().await {
        let trusted_proxy_cidrs = &config::get().listen.trusted_proxy_cidrs;

        for trusted_net in trusted_proxy_cidrs {
            if trusted_net.contains(&addr.ip()) {
                trace!(
                    ?addr,
                    ?trusted_net,
                    "connection is now considered coming from a trusted proxy"
                );
                return true;
            }
        }
    }
    false
}

pub(crate) async fn trusted_proxy_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    let trusted_proxy = extract_trusted_proxy(&mut parts).await;
    parts
        .extensions
        .insert::<TrustedProxy>(TrustedProxy(trusted_proxy));

    let request = Request::from_parts(parts, body);

    next.run(request).await
}
