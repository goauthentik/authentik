use axum::{
    Extension, RequestPartsExt,
    extract::{FromRequestParts, Request},
    http::{
        header::{FORWARDED, HOST},
        request::Parts,
        status::StatusCode,
    },
    middleware::Next,
    response::{IntoResponse, Response},
};
use forwarded_header_value::ForwardedHeaderValue;
use tracing::{Span, instrument};

use crate::axum::extract::trusted_proxy::TrustedProxy;

const X_FORWARDED_HOST: &str = "X-Forwarded-Host";

#[derive(Clone, Debug)]
pub(crate) struct Host(pub String);

impl<S> FromRequestParts<S> for Host
where S: Send + Sync
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(host)| host)
    }
}

#[instrument(skip_all)]
async fn extract_host(parts: &mut Parts) -> Result<String, (StatusCode, &'static str)> {
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
            return Ok(host.to_owned());
        }

        if let Some(forwarded) = parts.headers.get(FORWARDED)
            && let Ok(forwarded) = forwarded.to_str()
            && let Ok(forwarded) = ForwardedHeaderValue::from_forwarded(forwarded)
        {
            for stanza in forwarded.iter() {
                if let Some(forwarded_host) = &stanza.forwarded_host {
                    return Ok(forwarded_host.to_owned());
                }
            }
        }
    }

    if let Some(host) = parts.headers.get(HOST).and_then(|host| host.to_str().ok()) {
        return Ok(host.to_owned());
    }

    if let Some(host) = parts.uri.host() {
        Ok(host.to_owned())
    } else {
        Err((StatusCode::BAD_REQUEST, "missing host header"))
    }
}

pub(crate) async fn host_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    let host = match extract_host(&mut parts).await {
        Ok(host) => host,
        Err(err) => return err.into_response(),
    };
    Span::current().record("host", host.clone());
    parts.extensions.insert::<Host>(Host(host));

    let request = Request::from_parts(parts, body);

    next.run(request).await
}

#[cfg(test)]
mod tests {
    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn host_header() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("host", "example.com:8080")
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "example.com:8080",
        );
    }

    #[tokio::test]
    async fn from_uri() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com:8080/path")
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "example.com",
        );
    }

    #[tokio::test]
    async fn x_forwarded_host_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "forwarded.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "host=forwarded.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_host_untrusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "malicious.example.com")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "example.com",
        );
    }

    #[tokio::test]
    async fn forwarded_header_untrusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "host=malicious.example.com")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "example.com",
        );
    }

    #[tokio::test]
    async fn priority_order() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-host", "x-forwarded.example.com")
            .header("forwarded", "host=forwarded.example.com")
            .header("host", "host-header.example.com")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "x-forwarded.example.com",
        );
    }

    #[tokio::test]
    async fn no_host_found() {
        let (mut parts, _) = Request::builder()
            .uri("/path")
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_err());
        assert_eq!(result.expect_err("Host extract should fail").0, 400);
    }

    #[tokio::test]
    async fn multiple_forwarded_stanzas() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header(
                "forwarded",
                "host=first.example.com, host=second.example.com",
            )
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let result = extract_host(&mut parts).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Host extraction should succeed"),
            "first.example.com",
        );
    }
}
