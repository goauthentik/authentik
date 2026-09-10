//! axum extractor and middleware to retrieve the client IP.

use std::net::{IpAddr, Ipv6Addr, SocketAddr};

use axum::{
    Extension, RequestPartsExt as _,
    extract::{ConnectInfo, FromRequestParts, Request},
    http::{HeaderMap, request::Parts},
    middleware::Next,
    response::Response,
};
use tracing::{Span, instrument};

use crate::{
    accept::proxy_protocol::ProxyProtocolState,
    extract::trusted_proxy::{TrustedProxy, ip_addr_trusted},
};

/// Client IP.
///
/// The [`client_ip_middleware`] must be added to the router before using this extractor,
/// otherwise this will result in requests erroring.
#[derive(Clone, Copy, Debug)]
pub struct ClientIp(pub IpAddr);

impl<S> FromRequestParts<S> for ClientIp
where
    S: Send + Sync,
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(client_ip)| client_ip)
    }
}

/// Get the rightmost IP from the `X-Forwarded-For` chain that is not itself a
/// trusted proxy.
fn rightmost_untrusted_x_forwarded_for(headers: &HeaderMap) -> Option<IpAddr> {
    let mut forwarded_ips = Vec::new();
    for value in headers.get_all("x-forwarded-for") {
        let Ok(value) = value.to_str() else {
            continue;
        };
        for part in value.split(',') {
            let part = part.trim();
            let ip = if let Ok(ip) = part.parse::<IpAddr>() {
                ip
            } else if let Ok(socket_addr) = part.parse::<SocketAddr>() {
                socket_addr.ip()
            } else {
                continue;
            };
            forwarded_ips.push(ip);
        }
    }

    forwarded_ips
        .iter()
        .rev()
        .find(|ip| ip_addr_trusted(ip).is_none())
        .or_else(|| forwarded_ips.first())
        .copied()
}

/// Get the client IP from the request.
#[instrument(skip_all)]
async fn extract_client_ip(parts: &mut Parts) -> IpAddr {
    let is_trusted = parts
        .extract::<TrustedProxy>()
        .await
        .unwrap_or(TrustedProxy(false))
        .0;

    if is_trusted {
        if let Some(ip) = rightmost_untrusted_x_forwarded_for(&parts.headers) {
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
        // as default.
        Ipv6Addr::LOCALHOST.into()
    }
}

/// Middleware required by the [`ClientIp`] extractor.
///
/// Use with [`axum::middleware::from_fn`].
pub async fn client_ip_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    let client_ip = if let Some(client_ip) = parts.extensions.get::<ClientIp>() {
        client_ip
    } else {
        let client_ip = ClientIp(extract_client_ip(&mut parts).await);
        parts.extensions.insert(client_ip);
        parts.extensions.get::<ClientIp>().expect("infallible")
    };

    Span::current().record("remote", client_ip.0.to_string());

    let request = Request::from_parts(parts, body);

    next.run(request).await
}

#[cfg(test)]
mod tests {
    use std::net::Ipv4Addr;

    use ak_common::config;
    use axum::{body::Body, http::Request};

    use super::*;

    #[tokio::test]
    async fn x_forwarded_for_trusted() {
        config::init().expect("config");
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
    async fn headers_untrusted() {
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
        config::init().expect("config");
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
    async fn rightmost_untrusted_x_forwarded_for() {
        config::init().expect("config");
        // The proxy's own appended address is trusted (172.16.0.0/12 by
        // default), so the client to its left wins (#25393).
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "1.2.3.4, 172.17.0.1")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(1, 2, 3, 4));
    }

    #[tokio::test]
    async fn all_forwarded_for_entries_trusted_falls_back_to_leftmost() {
        config::init().expect("config");
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "10.0.0.9, 10.0.0.1")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(10, 0, 0, 9));
    }

    #[tokio::test]
    async fn multiple_x_forwarded_for() {
        config::init().expect("config");
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "192.0.2.1, 192.0.2.2, 192.0.2.3")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(192, 0, 2, 3));
    }

    #[tokio::test]
    async fn with_ports() {
        config::init().expect("config");
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "10.0.0.1:9000")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv4Addr::new(10, 0, 0, 1));
    }

    #[tokio::test]
    async fn ipv6_with_ports() {
        config::init().expect("config");
        let (mut parts, _) = Request::builder()
            .uri("http://example.com/path")
            .header("x-forwarded-for", "[2001:db8::42]:9000")
            .extension(TrustedProxy(true))
            .body(Body::empty())
            .expect("Failed to create request")
            .into_parts();

        let client_ip = extract_client_ip(&mut parts).await;

        assert_eq!(client_ip, Ipv6Addr::new(0x2001, 0xdb8, 0, 0, 0, 0, 0, 0x42));
    }
}
