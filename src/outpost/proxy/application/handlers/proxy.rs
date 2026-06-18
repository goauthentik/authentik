use std::sync::Arc;

use ak_axum::error::Result;
use ak_axum::extract::client_ip::ClientIp;
use ak_axum::extract::host::Host;
use axum::{
    extract::{Request, State},
    http::{HeaderName, HeaderValue, StatusCode},
    response::Response,
};
use tracing::{instrument, warn};
use url::Url;

use crate::outpost::proxy::{application::Application, error_page, oauth, reverse_proxy};

#[instrument(skip_all)]
pub(crate) async fn handle(
    State(app): State<Arc<Application>>,
    ClientIp(client_ip): ClientIp,
    Host(forwarded_host): Host,
    mut request: Request,
) -> Result<Response> {
    let claims = app.check_auth(request.headers()).await;

    if let Some(claims) = &claims {
        app.add_upstream_headers(request.headers_mut(), claims);
    } else {
        // Unauthenticated: allow only allowlisted paths through; otherwise start auth.
        let request_url =
            Url::parse(&oauth::url_join(&app.provider.external_host, request.uri().path())).ok();
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

    // A user attribute may override the upstream backend.
    let proxy_claims = claims.as_ref().and_then(|claims| claims.ak_proxy.as_ref());
    let target = proxy_claims
        .map(|proxy| proxy.backend_override.as_str())
        .filter(|backend| !backend.is_empty())
        .map_or_else(
            || app.provider.internal_host.clone().unwrap_or_default(),
            str::to_owned,
        );

    match reverse_proxy::call(client_ip, &target, request, &app.upstream_client).await {
        Ok(response) => Ok(response),
        Err(err) => {
            warn!(?err, "error proxying to upstream server");
            // Only superusers see the underlying error detail.
            let is_superuser = proxy_claims.is_some_and(|proxy| proxy.is_superuser);
            let message = if is_superuser {
                format!("Error proxying to upstream server: {err}")
            } else {
                "Failed to connect to backend.".to_owned()
            };
            Ok(error_page::error_response(
                StatusCode::BAD_GATEWAY,
                "Bad Gateway",
                &message,
            ))
        }
    }
}
