use std::convert::Infallible;

use axum::{
    RequestPartsExt,
    extract::{FromRequestParts, OptionalFromRequestParts},
    http::{self, StatusCode, header::FORWARDED, request::Parts},
};
use forwarded_header_value::{ForwardedHeaderValue, Protocol};

use crate::extract::trusted_proxy::TrustedProxy;

const X_FORWARDED_PROTO: &str = "X-Forwarded-Proto";
const X_FORWARDED_SCHEME: &str = "X-Forwarded-Scheme";

#[derive(Clone, Debug)]
pub struct Scheme(pub http::uri::Scheme);

impl<S> FromRequestParts<S> for Scheme
where S: Send + Sync
{
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        parts
            .extract::<Option<Self>>()
            .await
            .ok()
            .flatten()
            .ok_or((StatusCode::BAD_REQUEST, "No scheme found in request"))
    }
}

impl<S> OptionalFromRequestParts<S> for Scheme
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
            if let Some(proto) = parts.headers.get(X_FORWARDED_PROTO)
                && let Ok(proto) = proto.to_str()
                && let Ok(scheme) = proto.try_into()
            {
                return Ok(Some(Self(scheme)));
            }

            if let Some(proto) = parts.headers.get(X_FORWARDED_SCHEME)
                && let Ok(proto) = proto.to_str()
                && let Ok(scheme) = proto.try_into()
            {
                return Ok(Some(Self(scheme)));
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
                        return Ok(Some(Self(scheme)));
                    }
                }
            }
        }

        // TODO: don't use the URL here, instead look at whether the connection was made over TLS
        // or plaintext

        Ok(Some(Self(http::uri::Scheme::HTTP)))
    }
}
