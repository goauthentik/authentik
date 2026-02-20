use std::convert::Infallible;

use axum::{
    Extension, RequestPartsExt,
    extract::FromRequestParts,
    http::{self, header::FORWARDED, request::Parts},
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
    type Rejection = Infallible;

    #[instrument(skip_all)]
    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
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
                return Ok(Self(scheme));
            }

            if let Some(proto) = parts.headers.get(X_FORWARDED_SCHEME)
                && let Ok(proto) = proto.to_str()
                && let Ok(scheme) = proto.to_lowercase().as_str().try_into()
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

#[cfg(test)]
mod tests {
    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn x_forwarded_proto_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("scheme extraction should succeed").0,
            http::uri::Scheme::HTTPS,
        );
    }

    #[tokio::test]
    async fn x_forwarded_scheme_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-scheme", "https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("scheme extraction should succeed").0,
            http::uri::Scheme::HTTPS,
        );
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTPS,
        );
    }

    #[tokio::test]
    async fn x_forwarded_proto_untrusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "https")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTP,
        );
    }

    #[tokio::test]
    async fn scheme_from_tls_state() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .extension(TlsState {
                peer_certificates: None,
            })
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTPS,
        );
    }

    #[tokio::test]
    async fn scheme_defaults_to_http() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTP,
        );
    }

    #[tokio::test]
    async fn priority_order() {
        // Test that X-Forwarded-Proto takes priority over other headers when trusted
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "http")
            .header("x-forwarded-scheme", "https")
            .header("forwarded", "proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        // Should use X-Forwarded-Proto (http) since it has highest priority
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTP,
        );
    }

    #[tokio::test]
    async fn multiple_forwarded_stanzas() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "proto=http, proto=https")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTP,
        );
    }

    #[tokio::test]
    async fn test_scheme_case_insensitive() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-proto", "HTTPS")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = Scheme::from_request_parts(&mut req.into_parts().0, &()).await;

        assert!(result.is_ok());
        assert_eq!(
            result.expect("Scheme extraction should succeed").0,
            http::uri::Scheme::HTTPS,
        );
    }
}
