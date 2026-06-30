use std::sync::Arc;

use ak_axum::{
    error::Result,
    extract::{client_ip::ClientIp, host::Host},
};
use axum::{
    extract::{Request, State},
    http::{HeaderName, HeaderValue, StatusCode},
    response::Response,
};
use metrics::histogram;
use tokio::time::Instant;
use tracing::{instrument, warn};
use url::Url;

use crate::outpost::proxy::{application::Application, error_page, oauth, reverse_proxy};

#[instrument(skip_all, fields(user = tracing::field::Empty))]
pub(crate) async fn handle(
    State(app): State<Arc<Application>>,
    ClientIp(client_ip): ClientIp,
    Host(forwarded_host): Host,
    mut request: Request,
) -> Result<Response> {
    let auth = app.check_auth(request.headers()).await;
    let claims = auth.as_ref().map(|authed| &authed.claims);

    if let Some(claims) = claims {
        app.add_upstream_headers(request.headers_mut(), claims);
    } else {
        // Unauthenticated: allow only allowlisted paths through; otherwise start auth.
        let request_url = Url::parse(&oauth::url_join(
            &app.provider.external_host,
            request.uri().path(),
        ))
        .ok();
        if !request_url.is_some_and(|url| app.is_allowlisted(&url)) {
            return super::redirect_to_start(&app, request.headers(), request.uri());
        }
    }

    // Preserve the original (external) host for the upstream.
    if let Ok(host) = HeaderValue::from_str(&forwarded_host) {
        request
            .headers_mut()
            .insert(HeaderName::from_static("x-forwarded-host"), host);
    }

    // A user attribute may override the upstream backend and/or the host header.
    let proxy_claims = claims.and_then(|claims| claims.ak_proxy.as_ref());
    let target = proxy_claims
        .map(|proxy| proxy.backend_override.as_str())
        .filter(|backend| !backend.is_empty())
        .map_or_else(
            || app.provider.internal_host.clone().unwrap_or_default(),
            str::to_owned,
        );
    let host_override = proxy_claims
        .map(|proxy| proxy.host_header.as_str())
        .filter(|host| !host.is_empty());

    let method = request.method().to_string();
    let start = Instant::now();
    let call_result = reverse_proxy::call(
        client_ip,
        &target,
        request,
        host_override,
        &app.upstream_client,
    )
    .await;

    let (scheme, upstream_host) = Url::parse(&target)
        .map(|url| (url.scheme().to_owned(), url.authority().to_owned()))
        .unwrap_or_default();
    histogram!(
        "authentik_outpost_proxy_upstream_response_duration_seconds",
        "outpost_name" => app.outpost_name.clone(),
        "method" => method,
        "scheme" => scheme,
        "host" => forwarded_host,
        "upstream_host" => upstream_host,
    )
    .record(start.elapsed().as_secs_f64());

    let response = match call_result {
        Ok(response) => response,
        Err(err) => {
            warn!(?err, "error proxying to upstream server");
            // Only superusers see the underlying error detail.
            let is_superuser = proxy_claims.is_some_and(|proxy| proxy.is_superuser);
            let message = if is_superuser {
                format!("Error proxying to upstream server: {err}")
            } else {
                "Failed to connect to backend.".to_owned()
            };
            error_page::error_response(StatusCode::BAD_GATEWAY, "Bad Gateway", &message)
        }
    };

    // Emit the session cookie if header auth created a session for this request.
    let set_cookie = auth.and_then(|authed| authed.set_cookie);
    Ok(super::with_session_cookie(&app, set_cookie, response))
}
