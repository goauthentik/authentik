use std::convert::Infallible;

use axum::{
    Extension, RequestPartsExt,
    extract::FromRequestParts,
    http::{self, header::FORWARDED, request::Parts},
};
use forwarded_header_value::{ForwardedHeaderValue, Protocol};

use crate::{
    accept::{proxy_protocol::ProxyProtocolState, tls::TlsState},
    extract::trusted_proxy::TrustedProxy,
};

const X_FORWARDED_PROTO: &str = "X-Forwarded-Proto";
const X_FORWARDED_SCHEME: &str = "X-Forwarded-Scheme";

#[derive(Clone, Debug)]
pub struct Scheme(pub http::uri::Scheme);

impl<S> FromRequestParts<S> for Scheme
where
    S: Send + Sync,
{
    type Rejection = Infallible;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let is_trusted = parts
            .extract::<TrustedProxy>()
            .await
            .unwrap_or(TrustedProxy(false))
            .0;

        if is_trusted {
            if let Some(proto) = parts.headers.get(X_FORWARDED_PROTO)
                && let Ok(proto) = proto.to_str()
                && let Ok(scheme) = proto.try_into()
            {
                return Ok(Self(scheme));
            }

            if let Some(proto) = parts.headers.get(X_FORWARDED_SCHEME)
                && let Ok(proto) = proto.to_str()
                && let Ok(scheme) = proto.try_into()
            {
                return Ok(Self(scheme));
            }

            if let Some(forwarded) = parts.headers.get(FORWARDED)
                && let Ok(forwarded) = forwarded.to_str()
                && let Ok(forwarded) = ForwardedHeaderValue::from_forwarded(forwarded)
            {
                for stanza in forwarded.iter() {
                    if let Some(forwarded_proto) = &stanza.forwarded_proto {
                        let scheme = match forwarded_proto {
                            Protocol::Http => http::uri::Scheme::HTTP,
                            Protocol::Https => http::uri::Scheme::HTTPS,
                        };
                        return Ok(Self(scheme));
                    }
                }
            }

            if let Ok(Extension(proxy_protocol_state)) =
                parts.extract::<Extension<ProxyProtocolState>>().await
                && let Some(header) = &proxy_protocol_state.header
                && let Some(_) = header.ssl()
            {
                return Ok(Self(http::uri::Scheme::HTTPS));
            }
        }

        if parts.extract::<Extension<TlsState>>().await.is_ok() {
            Ok(Self(http::uri::Scheme::HTTPS))
        } else {
            Ok(Self(http::uri::Scheme::HTTP))
        }
    }
}
