use std::{convert::Infallible, net::SocketAddr};

use authentik_config::get_config;
use axum::{
    RequestPartsExt,
    extract::{ConnectInfo, FromRequestParts},
    http::request::Parts,
};
use tracing::trace;

#[derive(Clone, Copy, Debug)]
pub struct TrustedProxy(pub bool);

impl<S> FromRequestParts<S> for TrustedProxy
where S: Send + Sync
{
    type Rejection = Infallible;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        if let Some(res) = parts.extensions.get::<Self>() {
            return Ok(*res);
        }

        let mut res = Self(false);

        if let Ok(ConnectInfo(addr)) = parts.extract::<ConnectInfo<SocketAddr>>().await {
            let trusted_proxy_cidrs = &get_config().await.listen.trusted_proxy_cidrs;

            for trusted_net in trusted_proxy_cidrs {
                if trusted_net.contains(&addr.ip()) {
                    trace!(
                        ?addr,
                        ?trusted_net,
                        "connection is now considered coming from a trusted proxy"
                    );
                    res = Self(true);
                }
            }
        }

        parts.extensions.insert(res);

        Ok(res)
    }
}
