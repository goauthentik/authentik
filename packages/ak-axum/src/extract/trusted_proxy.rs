//! axum extractor and middleware to check if a request comes from a trusted proxy.

use std::net::{IpAddr, SocketAddr};

use ak_common::config;
use axum::{
    Extension, RequestPartsExt as _,
    extract::{ConnectInfo, FromRequestParts, Request},
    http::request::Parts,
    middleware::Next,
    response::Response,
};
use ipnet::IpNet;
use tracing::{instrument, trace};

/// Whether the request comes from a trusted proxy.
///
/// The [`trusted_proxy_middleware`] must be added to the router before using this extractor,
/// otherwise this will result in requests erroring.
#[derive(Clone, Copy, Debug)]
pub struct TrustedProxy(pub bool);

impl<S> FromRequestParts<S> for TrustedProxy
where
    S: Send + Sync,
{
    type Rejection = <Extension<Self> as FromRequestParts<S>>::Rejection;

    async fn from_request_parts(parts: &mut Parts, state: &S) -> Result<Self, Self::Rejection> {
        Extension::<Self>::from_request_parts(parts, state)
            .await
            .map(|Extension(trusted_proxy)| trusted_proxy)
    }
}

fn ip_addr_trusted(ip: &IpAddr) -> Option<IpNet> {
    let trusted_proxy_cidrs = &config::get().listen.trusted_proxy_cidrs;
    for net in trusted_proxy_cidrs {
        if net.contains(&ip.to_canonical()) {
            return Some(*net);
        }
    }
    None
}

/// Check whether the request comes from a trusted proxy.
#[instrument(skip_all)]
async fn extract_trusted_proxy(parts: &mut Parts) -> bool {
    if let Ok(ConnectInfo(addr)) = parts.extract::<ConnectInfo<SocketAddr>>().await
        && let Some(trusted_net) = ip_addr_trusted(&addr.ip())
    {
        trace!(
            ?addr,
            ?trusted_net,
            "connection is now considered coming from a trusted proxy"
        );
        return true;
    }
    false
}

/// Middleware required by the [`TrustedProxy`] extractor.
///
/// Use with [`axum::middleware::from_fn`].
pub async fn trusted_proxy_middleware(request: Request, next: Next) -> Response {
    let (mut parts, body) = request.into_parts();

    if parts.extensions.get::<TrustedProxy>().is_none() {
        let trusted_proxy = extract_trusted_proxy(&mut parts).await;
        parts
            .extensions
            .insert::<TrustedProxy>(TrustedProxy(trusted_proxy));
    }

    let request = Request::from_parts(parts, body);

    next.run(request).await
}

#[cfg(test)]
mod test {
    use std::net::IpAddr;

    use ak_common::config;

    use crate::extract::trusted_proxy::ip_addr_trusted;

    #[test]
    fn ipv4_mapped_ipv6_matches_ipv4_cidr() {
        config::init().expect("config");
        // IPv4-mapped IPv6 address within the IPv4 CIDR matches.
        let ip: IpAddr = "::ffff:10.2.0.229".parse().expect("valid IP");
        assert!(ip_addr_trusted(&ip).is_some());
        // An IPv4-mapped address outside the CIDR does not.
        let ip: IpAddr = "::ffff:11.0.0.1".parse().expect("valid IP");
        assert!(ip_addr_trusted(&ip).is_none());
    }
}
