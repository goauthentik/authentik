//! Reverse proxy, port from Go's httputil.ReverseProxy

use std::net::IpAddr;

use axum::body::Body;
use axum::http::header::{
    CONNECTION, Entry, HOST, HeaderMap, HeaderName, HeaderValue, InvalidHeaderValue,
    PROXY_AUTHENTICATE, PROXY_AUTHORIZATION, TE, TRAILER, TRANSFER_ENCODING, UPGRADE,
};
use axum::http::uri::InvalidUri;
use axum::http::{Request, Response, StatusCode, Uri};
use hyper::upgrade::OnUpgrade;
use hyper_util::client::legacy::Client;
use hyper_util::client::legacy::connect::Connect;
use hyper_util::rt::TokioIo;
use tokio::io::copy_bidirectional;
use tracing::warn;

const TRAILERS: HeaderName = HeaderName::from_static("trailers");
const X_FORWARDED_FOR: HeaderName = HeaderName::from_static("x-forwarded-for");
const HOP_HEADERS: [HeaderName; 9] = [
    CONNECTION,
    TE,
    TRAILER,
    HeaderName::from_static("keep-alive"),
    HeaderName::from_static("proxy-connection"),
    PROXY_AUTHENTICATE,
    PROXY_AUTHORIZATION,
    TRANSFER_ENCODING,
    UPGRADE,
];

#[derive(Debug, thiserror::Error)]
pub(super) enum ProxyError {
    #[error("invalid upstream uri: {0}")]
    InvalidUri(#[from] InvalidUri),
    #[error("upstream request failed: {0}")]
    Client(#[from] hyper_util::client::legacy::Error),
    #[error("invalid header value: {0}")]
    InvalidHeader(#[from] InvalidHeaderValue),
    #[error("protocol upgrade failed: {0}")]
    Upgrade(String),
}

fn remove_hop_headers(headers: &mut HeaderMap) {
    for header in &HOP_HEADERS {
        headers.remove(header);
    }
}

/// Remove headers named in the `Connection` header.
fn remove_connection_headers(headers: &mut HeaderMap) {
    let Some(value) = headers.get(CONNECTION).cloned() else {
        return;
    };
    let Ok(value) = value.to_str() else {
        return;
    };
    for name in value
        .split(',')
        .map(str::trim)
        .filter(|name| !name.is_empty())
    {
        headers.remove(name);
    }
}

/// The `Upgrade` header value, if the request/response requests a protocol upgrade.
fn upgrade_type(headers: &HeaderMap) -> Option<String> {
    let connection = headers.get(CONNECTION)?.to_str().ok()?;
    let requests_upgrade = connection
        .split(',')
        .any(|token| token.trim().eq_ignore_ascii_case(UPGRADE.as_str()));
    if !requests_upgrade {
        return None;
    }
    Some(headers.get(UPGRADE)?.to_str().ok()?.to_owned())
}

/// Combine `forward_url` with the request's path and query, merging query strings.
fn forward_uri<B>(forward_url: &str, request: &Request<B>) -> String {
    let (base, forward_query) = forward_url.split_once('?').unwrap_or((forward_url, ""));
    let base = base.strip_suffix('/').unwrap_or(base);
    let request_query = request.uri().query().unwrap_or_default();

    let mut url = String::with_capacity(base.len() + request.uri().path().len());
    url.push_str(base);
    url.push_str(request.uri().path());

    if forward_query.is_empty() && request_query.is_empty() {
        return url;
    }

    url.push('?');
    url.push_str(forward_query);
    if forward_query.is_empty() {
        url.push_str(request_query);
        return url;
    }

    // Append request query params whose keys are not already in the forward query.
    let forward_keys: Vec<&str> = forward_query
        .split('&')
        .map(|item| item.split_once('=').map_or(item, |(key, _)| key))
        .collect();
    for item in request_query.split('&') {
        let (key, value) = item.split_once('=').unwrap_or((item, ""));
        if !forward_keys.contains(&key) {
            url.push('&');
            url.push_str(key);
            url.push('=');
            url.push_str(value);
        }
    }
    url
}

fn create_proxied_request<B>(
    client_ip: IpAddr,
    forward_url: &str,
    mut request: Request<B>,
    upgrade: Option<&str>,
) -> Result<Request<B>, ProxyError> {
    let contains_te_trailers = request
        .headers()
        .get(TE)
        .and_then(|value| value.to_str().ok())
        .is_some_and(|te| {
            te.split(',')
                .any(|token| token.trim().eq_ignore_ascii_case(TRAILERS.as_str()))
        });

    let uri: Uri = forward_uri(forward_url, &request).parse()?;
    // The client sets `Host` from the URI authority.
    request.headers_mut().remove(HOST);
    *request.uri_mut() = uri;

    remove_hop_headers(request.headers_mut());
    remove_connection_headers(request.headers_mut());

    if contains_te_trailers {
        request
            .headers_mut()
            .insert(TE, HeaderValue::from_static("trailers"));
    }

    if let Some(upgrade) = upgrade {
        request.headers_mut().insert(UPGRADE, upgrade.parse()?);
        request
            .headers_mut()
            .insert(CONNECTION, HeaderValue::from_static("upgrade"));
    }

    match request.headers_mut().entry(&X_FORWARDED_FOR) {
        Entry::Vacant(entry) => {
            entry.insert(client_ip.to_string().parse()?);
        }
        Entry::Occupied(mut entry) => {
            let forwarded = format!("{}, {client_ip}", entry.get().to_str().unwrap_or_default());
            entry.insert(forwarded.parse()?);
        }
    }

    Ok(request)
}

/// Proxy `request` to `forward_uri`, handling protocol upgrades (e.g. WebSocket).
pub(super) async fn call<C>(
    client_ip: IpAddr,
    forward_uri: &str,
    mut request: Request<Body>,
    client: &Client<C, Body>,
) -> Result<Response<Body>, ProxyError>
where
    C: Connect + Clone + Send + Sync + 'static,
{
    let request_upgrade_type = upgrade_type(request.headers());
    let request_on_upgrade = request.extensions_mut().remove::<OnUpgrade>();

    let proxied = create_proxied_request(
        client_ip,
        forward_uri,
        request,
        request_upgrade_type.as_deref(),
    )?;
    let mut response = client.request(proxied).await?;

    if response.status() != StatusCode::SWITCHING_PROTOCOLS {
        remove_hop_headers(response.headers_mut());
        remove_connection_headers(response.headers_mut());
        return Ok(response.map(Body::new));
    }

    // Protocol upgrade: bridge the two upgraded connections.
    let response_upgrade_type = upgrade_type(response.headers());
    if request_upgrade_type != response_upgrade_type {
        return Err(ProxyError::Upgrade(format!(
            "backend switched to {response_upgrade_type:?} when {request_upgrade_type:?} was requested"
        )));
    }
    let Some(request_on_upgrade) = request_on_upgrade else {
        return Err(ProxyError::Upgrade(
            "request has no upgrade extension".to_owned(),
        ));
    };
    let response_on_upgrade = response
        .extensions_mut()
        .remove::<OnUpgrade>()
        .ok_or_else(|| ProxyError::Upgrade("response has no upgrade extension".to_owned()))?;

    tokio::spawn(async move {
        let (downstream, upstream) = match (request_on_upgrade.await, response_on_upgrade.await) {
            (Ok(downstream), Ok(upstream)) => (downstream, upstream),
            (Err(err), _) | (_, Err(err)) => {
                warn!(?err, "failed to upgrade connection");
                return;
            }
        };
        if let Err(err) =
            copy_bidirectional(&mut TokioIo::new(downstream), &mut TokioIo::new(upstream)).await
        {
            warn!(?err, "error copying between upgraded connections");
        }
    });

    Ok(response.map(Body::new))
}
