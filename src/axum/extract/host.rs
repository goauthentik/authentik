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
use tracing::instrument;

use crate::axum::extract::trusted_proxy::TrustedProxy;

const X_FORWARDED_HOST: &str = "X-Forwarded-Host";

#[derive(Clone, Debug)]
pub(crate) struct Host(pub String);

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

    #[instrument(skip_all)]
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

#[cfg(test)]
mod tests {
    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn host_header() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("host", "example.com:8080")
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "example.com:8080",
        );
    }

    #[tokio::test]
    async fn from_uri() {
        let req = Request::builder()
            .uri("http://example.com:8080/path")
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "example.com",
        );
    }

    #[tokio::test]
    async fn x_forwarded_host_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "forwarded.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "host=forwarded.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_host_untrusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "malicious.example.com")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_header_untrusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "host=malicious.example.com")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "example.com",
        );
    }

    #[tokio::test]
    async fn priority_order() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "x-forwarded.example.com")
            .header("forwarded", "host=forwarded.example.com")
            .header("host", "host-header.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "x-forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn no_host_found() {
        let req = Request::builder()
            .uri("/path")
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_err());
        assert_eq!(
            result.expect_err("Should fail when no host found").0,
            StatusCode::BAD_REQUEST,
        );
    }

    #[tokio::test]
    async fn multiple_forwarded_stanzas() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header(
                "forwarded",
                "host=first.example.com, host=second.example.com",
            )
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <Host as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed").0,
            "first.example.com",
        );
    }
}
