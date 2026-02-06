use std::{
    convert::Infallible,
    net::{IpAddr, SocketAddr},
};

use axum::{
    Extension, RequestPartsExt,
    extract::{ConnectInfo, FromRequestParts, OptionalFromRequestParts},
    http::{StatusCode, request::Parts},
};

use crate::{accept::proxy_protocol::ProxyProtocolState, extract::trusted_proxy::TrustedProxy};

#[derive(Clone, Debug)]
pub struct ClientIP(pub IpAddr);

impl<S> FromRequestParts<S> for ClientIP
where S: Send + Sync
{
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        parts
            .extract::<Option<ClientIP>>()
            .await
            .ok()
            .flatten()
            .ok_or((StatusCode::BAD_REQUEST, "No client IP found in request"))
    }
}

impl<S> OptionalFromRequestParts<S> for ClientIP
where S: Send + Sync
{
    type Rejection = Infallible;

    async fn from_request_parts(
        parts: &mut Parts,
        _state: &S,
    ) -> Result<Option<Self>, Self::Rejection> {
        let is_trusted = parts
            .extract::<TrustedProxy>()
            .await
            .unwrap_or(TrustedProxy(false))
            .0;

        if is_trusted {
            if let Ok(ip) = client_ip::rightmost_x_forwarded_for(&parts.headers) {
                return Ok(Some(Self(ip)));
            }

            if let Ok(ip) = client_ip::x_real_ip(&parts.headers) {
                return Ok(Some(Self(ip)));
            }

            if let Ok(ip) = client_ip::rightmost_forwarded(&parts.headers) {
                return Ok(Some(Self(ip)));
            }

            if let Ok(Extension(proxy_protocol_state)) =
                parts.extract::<Extension<ProxyProtocolState>>().await
                && let Some(header) = &proxy_protocol_state.header
                && let Some(addr) = header.proxied_address()
            {
                return Ok(Some(Self(addr.source.ip())));
            }
        }

        if let Ok(ConnectInfo(addr)) = parts.extract::<ConnectInfo<SocketAddr>>().await {
            return Ok(Some(Self(addr.ip())));
        }

        Ok(None)
    }
}
