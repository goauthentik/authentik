use std::net::{IpAddr, Ipv6Addr, SocketAddr};

use axum::{
    Extension, RequestPartsExt,
    extract::{ConnectInfo, FromRequestParts, Request},
    http::request::Parts,
    middleware::Next,
    response::Response,
};
use tracing::instrument;

use crate::axum::{
    accept::proxy_protocol::ProxyProtocolState, extract::trusted_proxy::TrustedProxy,
};

#[derive(Clone, Copy, Debug)]
pub(crate) struct ClientIp(pub IpAddr);

impl<S> FromRequestParts<S> for ClientIp
where S: Send + Sync
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(client_ip)| client_ip)
    }
}

#[instrument(skip_all)]
async fn extract_client_ip(parts: &mut Parts) -> IpAddr {
    let is_trusted = parts
        .extract::<TrustedProxy>()
        .await
        .unwrap_or(TrustedProxy(false))
        .0;

    if is_trusted {
        if let Ok(ip) = client_ip::rightmost_x_forwarded_for(&parts.headers) {
            return ip;
        }

        if let Ok(ip) = client_ip::x_real_ip(&parts.headers) {
            return ip;
        }

        if let Ok(ip) = client_ip::rightmost_forwarded(&parts.headers) {
            return ip;
        }

        if let Ok(Extension(proxy_protocol_state)) =
            parts.extract::<Extension<ProxyProtocolState>>().await
            && let Some(header) = &proxy_protocol_state.header
            && let Some(addr) = header.proxied_address()
        {
            return addr.source.ip();
        }
    }

    if let Ok(ConnectInfo(addr)) = parts.extract::<ConnectInfo<SocketAddr>>().await {
        addr.ip()
    } else {
        // No connect info means we received a request via a Unix socket, hence localhost
        // as default
        Ipv6Addr::LOCALHOST.into()
    }
}

pub(crate) async fn client_ip_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    let client_ip = extract_client_ip(&mut parts).await;
    parts.extensions.insert::<ClientIp>(ClientIp(client_ip));

    let request = Request::from_parts(parts, body);

    next.run(request).await
}

#[cfg(test)]
mod tests {
    use std::net::{Ipv4Addr, Ipv6Addr};

    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn x_forwarded_for_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.51, 192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 42),);
    }

    #[tokio::test]
    async fn x_real_ip_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-real-ip", "192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 42),);
    }

    #[tokio::test]
    async fn forwarded_header_trusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("forwarded", "for=192.0.2.42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 42),);
    }

    #[tokio::test]
    async fn from_connect_info() {
        let connect_addr: SocketAddr = "192.0.2.42:34932"
            .parse()
            .expect("Failed to parse socket address");
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .extension(ConnectInfo(connect_addr))
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 42),);
    }

    #[tokio::test]
    async fn headers_unstrusted() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.42")
            .extension(TrustedProxy(false))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv6Addr::LOCALHOST);
    }

    #[tokio::test]
    async fn priority_order() {
        // Test that X-Forwarded-For takes priority over other headers when trusted
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.1")
            .header("x-real-ip", "192.0.2.2")
            .header("forwarded", "for=192.0.2.3")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 1),);
    }

    #[tokio::test]
    async fn no_ip_found() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv6Addr::LOCALHOST);
    }

    #[tokio::test]
    async fn ipv6() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "2001:db8::42")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv6Addr::new(0x2001, 0xdb8, 0, 0, 0, 0, 0, 0x42),);
    }

    #[tokio::test]
    async fn multiple_x_forwarded_for() {
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.1, 192.0.2.2, 192.0.2.3")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 3),);
    }
}
