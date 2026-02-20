use std::{
    convert::Infallible,
    net::{IpAddr, SocketAddr},
};

use axum::{
    Extension, RequestPartsExt,
    extract::{ConnectInfo, FromRequestParts, OptionalFromRequestParts},
    http::{StatusCode, request::Parts},
};
use tracing::instrument;

use crate::axum::{
    accept::proxy_protocol::ProxyProtocolState, extract::trusted_proxy::TrustedProxy,
};

#[derive(Clone, Debug)]
pub(crate) struct ClientIP(pub IpAddr);

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

#[cfg(test)]
mod tests {
    use std::net::{Ipv4Addr, Ipv6Addr};

    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn x_forwarded_for_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.51, 192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 42),
        );
    }

    #[tokio::test]
    async fn x_real_ip_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-real-ip", "192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 42),
        );
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "for=192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 42),
        );
    }

    #[tokio::test]
    async fn from_connect_info() {
        let connect_addr: SocketAddr = "192.0.2.42:34932"
            .parse()
            .expect("Failed to parse socket address");
        let req = Request::builder()
            .uri("http://example.com/path")
            .extension(ConnectInfo(connect_addr))
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 42),
        );
    }

    #[tokio::test]
    async fn headers_unstrusted() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.42")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;
        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_none());
    }

    #[tokio::test]
    async fn priority_order() {
        // Test that X-Forwarded-For takes priority over other headers when trusted
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.1")
            .header("x-real-ip", "192.0.2.2")
            .header("forwarded", "for=192.0.2.3")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 1),
        );
    }

    #[tokio::test]
    async fn no_ip_found() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .body(Body::empty())
            .expect("Failed to create request");

        let result =
            <ClientIP as FromRequestParts<()>>::from_request_parts(&mut req.into_parts().0, &())
                .await;
        assert!(result.is_err());
        assert_eq!(
            result.expect_err("Should fail when no client IP found").0,
            StatusCode::BAD_REQUEST,
        );
    }

    #[tokio::test]
    async fn ipv6() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "2001:db8::42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv6Addr::new(0x2001, 0xdb8, 0, 0, 0, 0, 0, 0x42),
        );
    }

    #[tokio::test]
    async fn multiple_x_forwarded_for() {
        let req = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.1, 192.0.2.2, 192.0.2.3")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request");

        let result = <Option<ClientIP> as FromRequestParts<()>>::from_request_parts(
            &mut req.into_parts().0,
            &(),
        )
        .await;

        assert!(result.is_ok());
        let client_ip = result.expect("Client IP extraction should succeed");
        assert!(client_ip.is_some());
        // Should use rightmost IP
        assert_eq!(
            client_ip.expect("Client IP should be Some").0,
            Ipv4Addr::new(192, 0, 2, 3),
        );
    }
}
