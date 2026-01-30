use std::convert::Infallible;

use axum::{
    RequestPartsExt,
    extract::{FromRequestParts, OptionalFromRequestParts},
    http::{
        StatusCode,
        header::{FORWARDED, HOST},
        request::Parts,
    },
};
use forwarded_header_value::ForwardedHeaderValue;

use crate::extract::trusted_proxy::TrustedProxy;

const X_FORWARDED_HOST: &str = "X-Forwarded-Host";

#[derive(Clone, Debug)]
pub struct Host(pub String);

impl<S> FromRequestParts<S> for Host
where S: Send + Sync
{
    type Rejection = (StatusCode, &'static str);

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        parts
            .extract::<Option<Self>>()
            .await
            .ok()
            .flatten()
            .ok_or((StatusCode::BAD_REQUEST, "No host found in request"))
    }
}

impl<S> OptionalFromRequestParts<S> for Host
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
            if let Some(host) = parts
                .headers
                .get(X_FORWARDED_HOST)
                .and_then(|host| host.to_str().ok())
            {
                return Ok(Some(Self(host.to_owned())));
            }

            if let Some(forwarded) = parts.headers.get(FORWARDED)
                && let Ok(forwarded) = forwarded.to_str()
                && let Ok(forwarded) = ForwardedHeaderValue::from_forwarded(forwarded)
            {
                for stanza in forwarded.iter() {
                    if let Some(forwarded_host) = &stanza.forwarded_host {
                        return Ok(Some(Self(forwarded_host.to_owned())));
                    }
                }
            }
        }

        if let Some(host) = parts.headers.get(HOST).and_then(|host| host.to_str().ok()) {
            return Ok(Some(Self(host.to_owned())));
        }

        if let Some(host) = parts.uri.host() {
            return Ok(Some(Self(host.to_owned())));
        }

        Ok(None)
    }
}
