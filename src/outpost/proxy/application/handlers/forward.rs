use std::{net::IpAddr, sync::Arc};

use ak_axum::{error::Result, extract::client_ip::ClientIp};
use axum::{
    extract::{Request, State},
    http::{HeaderMap, StatusCode, Uri, header},
    response::{IntoResponse as _, Response},
};
use eyre::{Result as EyreResult, eyre};
use tracing::instrument;
use url::Url;

use crate::outpost::proxy::{application::Application, auth::Authenticated, oauth};

fn header_str<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    headers.get(name)?.to_str().ok()
}

/// Build the forwarded URL from Traefik/Caddy `X-Forwarded-*` headers.
pub(super) fn traefik_forward_url(headers: &HeaderMap) -> EyreResult<Url> {
    let proto = header_str(headers, "x-forwarded-proto").unwrap_or_default();
    let host = header_str(headers, "x-forwarded-host").unwrap_or_default();
    let uri = header_str(headers, "x-forwarded-uri").unwrap_or_default();
    Ok(Url::parse(&format!("{proto}://{host}{uri}"))?)
}

/// Build the forwarded URL from nginx's `X-Original-URL` header.
pub(super) fn nginx_forward_url(headers: &HeaderMap) -> EyreResult<Url> {
    let original =
        header_str(headers, "x-original-url").ok_or_else(|| eyre!("no forward URL found"))?;
    Ok(Url::parse(original)?)
}

/// Path prefix Envoy's external authorization filter sends requests under.
const ENVOY_PREFIX: &str = "/outpost.goauthentik.io/auth/envoy";

/// Reconstruct the original request URL from an Envoy ext-authz request: strip
/// the envoy prefix from the path and take the host from the `Host` header.
pub(super) fn envoy_forward_url(uri: &Uri, headers: &HeaderMap) -> Option<Url> {
    let path = uri
        .path()
        .strip_prefix(ENVOY_PREFIX)
        .filter(|path| !path.is_empty())
        .unwrap_or("/");
    let host = header_str(headers, "host")?;
    let scheme = uri
        .scheme_str()
        .or_else(|| header_str(headers, "x-forwarded-proto"))
        .unwrap_or("https");
    let query = uri
        .query()
        .map_or_else(String::new, |query| format!("?{query}"));
    Url::parse(&format!("{scheme}://{host}{path}{query}")).ok()
}

/// 200 response carrying the authenticated user's headers for the reverse proxy.
fn forward_authenticated_response(
    app: &Application,
    authed: &Authenticated,
    request_headers: &HeaderMap,
) -> Response {
    let mut response = StatusCode::OK.into_response();
    app.add_upstream_headers(
        response.headers_mut(),
        &authed.claims,
        authed.set_cookie.is_some(),
    );
    if let Some(user_agent) = request_headers.get(header::USER_AGENT) {
        response
            .headers_mut()
            .insert(header::USER_AGENT, user_agent.clone());
    }
    super::with_session_cookie(app, authed.set_cookie.clone(), response)
}

/// Shared Traefik/Caddy forward-auth flow (both reconstruct the URL from
/// `X-Forwarded-*` headers).
async fn forward_header_auth(
    app: Arc<Application>,
    mut request: Request,
    source: &str,
    client_ip: IpAddr,
) -> Result<Response> {
    let Ok(fwd) = traefik_forward_url(request.headers()) else {
        let message = format!(
            "Outpost {} (Provider {}) failed to detect a forward URL from {source}",
            app.outpost_name, app.provider.name
        );
        app.report_misconfiguration(
            &message,
            &request.uri().to_string(),
            request.headers(),
            client_ip,
        )
        .await;
        return Ok((StatusCode::INTERNAL_SERVER_ERROR, "configuration error").into_response());
    };

    if oauth::has_signature(fwd.query(), oauth::CALLBACK_SIGNATURE) {
        // The callback comes through the forward-auth endpoint; point the request
        // at the reconstructed URL so the handler sees `state`/`code`.
        if let Ok(uri) = Uri::try_from(fwd.as_str()) {
            *request.uri_mut() = uri;
        }
        return super::handle_auth_callback(State(app), request).await;
    }
    if oauth::has_signature(fwd.query(), oauth::LOGOUT_SIGNATURE) {
        return super::handle_sign_out(State(app), request).await;
    }

    if let Some(authed) = app.check_auth(request.headers()).await {
        return Ok(forward_authenticated_response(
            &app,
            &authed,
            request.headers(),
        ));
    }
    if app.is_allowlisted(&fwd) {
        return Ok(StatusCode::OK.into_response());
    }

    super::auth_start(&app, request.headers(), fwd.into())
}

#[instrument(skip_all, fields(user = tracing::field::Empty))]
pub(crate) async fn handle_caddy(
    State(app): State<Arc<Application>>,
    ClientIp(client_ip): ClientIp,
    request: Request,
) -> Result<Response> {
    forward_header_auth(app, request, "Caddy", client_ip).await
}

#[instrument(skip_all, fields(user = tracing::field::Empty))]
pub(crate) async fn handle_envoy(
    State(app): State<Arc<Application>>,
    request: Request,
) -> Result<Response> {
    let Some(fwd) = envoy_forward_url(request.uri(), request.headers()) else {
        return Ok((StatusCode::BAD_REQUEST, "invalid envoy request").into_response());
    };

    if let Some(authed) = app.check_auth(request.headers()).await {
        return Ok(forward_authenticated_response(
            &app,
            &authed,
            request.headers(),
        ));
    }
    if app.is_allowlisted(&fwd) {
        return Ok(StatusCode::OK.into_response());
    }

    super::auth_start(&app, request.headers(), fwd.into())
}

#[instrument(skip_all, fields(user = tracing::field::Empty))]
pub(crate) async fn handle_nginx(
    State(app): State<Arc<Application>>,
    ClientIp(client_ip): ClientIp,
    request: Request,
) -> Result<Response> {
    let Ok(fwd) = nginx_forward_url(request.headers()) else {
        let message = format!(
            "Outpost {} (Provider {}) failed to detect a forward URL from nginx",
            app.outpost_name, app.provider.name
        );
        app.report_misconfiguration(
            &message,
            &request.uri().to_string(),
            request.headers(),
            client_ip,
        )
        .await;
        return Ok((StatusCode::INTERNAL_SERVER_ERROR, "configuration error").into_response());
    };

    if let Some(authed) = app.check_auth(request.headers()).await {
        return Ok(forward_authenticated_response(
            &app,
            &authed,
            request.headers(),
        ));
    }
    if app.is_allowlisted(&fwd) {
        return Ok(StatusCode::OK.into_response());
    }
    // Let the outpost's own endpoints (callback, start, ...) through unauthenticated.
    if fwd.path().starts_with("/outpost.goauthentik.io") {
        return Ok(StatusCode::OK.into_response());
    }

    // nginx's auth_request performs the redirect itself, so just deny here.
    Ok((StatusCode::UNAUTHORIZED, "unauthorized request").into_response())
}

#[instrument(skip_all, fields(user = tracing::field::Empty))]
pub(crate) async fn handle_traefik(
    State(app): State<Arc<Application>>,
    ClientIp(client_ip): ClientIp,
    request: Request,
) -> Result<Response> {
    forward_header_auth(app, request, "Traefik", client_ip).await
}

#[cfg(test)]
mod tests {
    use axum::http::{HeaderMap, HeaderValue, Uri};

    use super::{ENVOY_PREFIX, envoy_forward_url, nginx_forward_url, traefik_forward_url};

    #[test]
    fn parses_traefik_forward_url() {
        let mut headers = HeaderMap::new();
        headers.insert("x-forwarded-proto", HeaderValue::from_static("https"));
        headers.insert(
            "x-forwarded-host",
            HeaderValue::from_static("app.example.com"),
        );
        headers.insert("x-forwarded-uri", HeaderValue::from_static("/foo?bar=1"));

        let url = traefik_forward_url(&headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/foo?bar=1");
    }

    #[test]
    fn traefik_without_headers_errors() {
        let _ = traefik_forward_url(&HeaderMap::new()).expect_err("missing headers should error");
    }

    #[test]
    fn parses_nginx_forward_url() {
        let mut headers = HeaderMap::new();
        headers.insert(
            "x-original-url",
            HeaderValue::from_static("https://app.example.com/app"),
        );

        let url = nginx_forward_url(&headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/app");
    }

    #[test]
    fn nginx_without_header_errors() {
        let _ = nginx_forward_url(&HeaderMap::new()).expect_err("missing header should error");
    }

    #[test]
    fn builds_envoy_forward_url() {
        let uri: Uri = "/outpost.goauthentik.io/auth/envoy/app/page?x=1"
            .parse()
            .expect("uri");
        let mut headers = HeaderMap::new();
        headers.insert("host", HeaderValue::from_static("app.example.com"));

        let url = envoy_forward_url(&uri, &headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/app/page?x=1");
    }

    #[test]
    fn envoy_bare_prefix_maps_to_root() {
        let uri: Uri = ENVOY_PREFIX.parse().expect("uri");
        let mut headers = HeaderMap::new();
        headers.insert("host", HeaderValue::from_static("app.example.com"));

        let url = envoy_forward_url(&uri, &headers).expect("forward url");
        assert_eq!(url.as_str(), "https://app.example.com/");
    }
}
