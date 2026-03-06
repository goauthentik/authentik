use axum::{
    Extension, RequestPartsExt,
    extract::{FromRequestParts, Request},
    http::{self, header::FORWARDED, request::Parts},
    middleware::Next,
    response::Response,
};
use forwarded_header_value::{ForwardedHeaderValue, Protocol};
use tracing::instrument;

use crate::axum::{
    accept::{proxy_protocol::ProxyProtocolState, tls::TlsState},
    extract::trusted_proxy::TrustedProxy,
};

const X_FORWARDED_PROTO: &str = "X-Forwarded-Proto";
const X_FORWARDED_SCHEME: &str = "X-Forwarded-Scheme";

#[derive(Clone, Debug)]
pub(crate) struct Scheme(pub http::uri::Scheme);

impl<S> FromRequestParts<S> for Scheme
where S: Send + Sync
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(scheme)| scheme)
    }
}

#[instrument(skip_all)]
async fn extract_scheme(parts: &mut Parts) -> http::uri::Scheme {
    let is_trusted = parts
        .extract::<TrustedProxy>()
        .await
        .unwrap_or(TrustedProxy(false))
        .0;

    if is_trusted {
        if let Some(proto) = parts.headers.get(X_FORWARDED_PROTO)
            && let Ok(proto) = proto.to_str()
            && let Ok(scheme) = proto.to_lowercase().as_str().try_into()
        {
            return scheme;
        }

        if let Some(proto) = parts.headers.get(X_FORWARDED_SCHEME)
            && let Ok(proto) = proto.to_str()
            && let Ok(scheme) = proto.to_lowercase().as_str().try_into()
        {
            return scheme;
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
                    return scheme;
                }
            }
        }

        if let Ok(Extension(proxy_protocol_state)) =
            parts.extract::<Extension<ProxyProtocolState>>().await
            && let Some(header) = &proxy_protocol_state.header
            && let Some(_) = header.ssl()
        {
            return http::uri::Scheme::HTTPS;
        }
    }

    if parts.extract::<Extension<TlsState>>().await.is_ok() {
        http::uri::Scheme::HTTPS
    } else {
        http::uri::Scheme::HTTP
    }
}

pub(crate) async fn scheme_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    let scheme = extract_scheme(&mut parts).await;
    parts.extensions.insert::<Scheme>(Scheme(scheme));

    let request = Request::from_parts(parts, body);

    next.run(request).await
}

#[cfg(test)]
mod tests {
    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn x_forwarded_proto_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTPS,);
    }

    #[tokio::test]
    async fn x_forwarded_scheme_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-scheme", "https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTPS,);
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTPS,);
    }

    #[tokio::test]
    async fn x_forwarded_proto_untrusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "https")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTP,);
    }

    #[tokio::test]
    async fn scheme_from_tls_state() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .extension(TlsState {
                peer_certificates: None,
            })
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTPS,);
    }

    #[tokio::test]
    async fn scheme_defaults_to_http() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTP,);
    }

    #[tokio::test]
    async fn priority_order() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "http")
            .header("x-forwarded-scheme", "https")
            .header("forwarded", "proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTP,);
    }

    #[tokio::test]
    async fn multiple_forwarded_stanzas() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "proto=http, proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTP,);
    }

    #[tokio::test]
    async fn test_scheme_case_insensitive() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "HTTPS")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let scheme = extract_scheme(&mut parts).await;

        assert_eq!(scheme, http::uri::Scheme::HTTPS,);
    }
}
