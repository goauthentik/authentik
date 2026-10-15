use std::sync::{Arc, LazyLock};

use ak_axum::{
    accept::tls::TlsState,
    error::Result,
    extract::{client_ip::ClientIp, host::Host, scheme::Scheme, trusted_proxy::TrustedProxy},
    router::wrap_router,
};
use ak_common::{config, db};
use axum::{
    Extension, Router,
    extract::{OriginalUri, Request, State},
    http::{
        HeaderMap, HeaderName, HeaderValue, Method, StatusCode, Uri,
        header::{
            ACCEPT, CONNECTION, CONTENT_TYPE, HOST, LOCATION, RETRY_AFTER, SEC_WEBSOCKET_KEY,
            SEC_WEBSOCKET_VERSION, UPGRADE,
        },
    },
    response::{IntoResponse as _, Response},
    routing::any,
};
use serde_json::json;
use tracing::{instrument, warn};

use crate::server::{Server, asgi::Peer};

static STARTUP_RESPONSE_JSON: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(RETRY_AFTER, "5")
        .header(CONTENT_TYPE, "application/json")
        .body(
            json!({
                "error": "authentik starting",
            })
            .to_string(),
        )
        .expect("infallible")
});

static STARTUP_RESPONSE_HTML: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/html")
        .body(include_str!("../../web/dist/standalone/loading/startup.html").to_owned())
        .expect("infallible")
});

static STARTUP_RESPONSE_PLAIN: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/plain")
        .body("authentik starting".to_owned())
        .expect("infallible")
});

const X_FORWARDED_CLIENT_CERT: HeaderName = HeaderName::from_static("x-forwarded-client-cert");
const X_FORWARDED_FOR: HeaderName = HeaderName::from_static("x-forwarded-for");
const X_FORWARDED_PROTO: HeaderName = HeaderName::from_static("x-forwarded-proto");

fn is_django_http_method(method: &Method) -> bool {
    matches!(
        method.as_str(),
        "GET" | "HEAD" | "POST" | "PUT" | "PATCH" | "DELETE" | "OPTIONS" | "TRACE"
    )
}

const FORWARD_ALWAYS_REMOVED_HEADERS: [HeaderName; 7] = [
    HeaderName::from_static("forwarded"),
    HeaderName::from_static("host"),
    X_FORWARDED_FOR,
    HeaderName::from_static("x-forwarded-host"),
    X_FORWARDED_PROTO,
    HeaderName::from_static("x-forwarded-scheme"),
    HeaderName::from_static("x-real-ip"),
];
const FORWARD_REMOVED_HEADERS_IF_UNTRUSTED: [HeaderName; 3] = [
    HeaderName::from_static("ssl-client-cert"), // nginx-ingress
    HeaderName::from_static("x-forwarded-tls-client-cert"), // traefik
    X_FORWARDED_CLIENT_CERT,                    // envoy
];

fn startup_response(accept_header: &str) -> Response {
    let response = if accept_header.contains("application/json") {
        STARTUP_RESPONSE_JSON.clone()
    } else if accept_header.contains("text/html") {
        STARTUP_RESPONSE_HTML.clone()
    } else {
        STARTUP_RESPONSE_PLAIN.clone()
    };

    let (parts, body) = response.into_parts();
    Response::from_parts(parts, body.into())
}

#[expect(
    clippy::too_many_arguments,
    reason = "We need all that data to forward the request properly"
)]
async fn forward_request(
    ClientIp(client_ip): ClientIp,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(server): State<Arc<Server>>,
    TrustedProxy(trusted_proxy): TrustedProxy,
    tls_state: Option<Extension<TlsState>>,
    OriginalUri(uri): OriginalUri,
    mut request: Request,
) -> Result<Response> {
    let accept_header = request
        .headers()
        .get(ACCEPT)
        .map(|v| v.to_str().unwrap_or_default().to_owned())
        .unwrap_or_default();

    let Some(asgi) = server.asgi.load_full() else {
        return Ok(startup_response(&accept_header));
    };
    if !is_django_http_method(request.method()) {
        return Ok((StatusCode::NOT_IMPLEMENTED, "Unsupported HTTP method.\n").into_response());
    }

    *request.uri_mut() = Uri::builder()
        .path_and_query(uri.path_and_query().map_or("/", |x| x.as_str()))
        .build()?;

    for header_name in FORWARD_ALWAYS_REMOVED_HEADERS {
        request.headers_mut().remove(header_name);
    }
    if !trusted_proxy {
        for header_name in FORWARD_REMOVED_HEADERS_IF_UNTRUSTED {
            request.headers_mut().remove(header_name);
        }
    }

    request.headers_mut().insert(
        X_FORWARDED_FOR,
        HeaderValue::from_str(&client_ip.to_string())?,
    );
    request
        .headers_mut()
        .insert(HOST, HeaderValue::from_str(&host)?);
    request
        .headers_mut()
        .insert(X_FORWARDED_PROTO, HeaderValue::from_str(scheme.as_ref())?);

    if let Some(tls_state) = tls_state
        && let Some(peer_certificates) = &tls_state.peer_certificates
    {
        let xfcc = peer_certificates
            .iter()
            .map(|cert| {
                let pem_encoded = pem::encode(&pem::Pem::new("CERTIFICATE", cert.as_ref()));
                let url_encoded: String =
                    url::form_urlencoded::byte_serialize(pem_encoded.as_bytes()).collect();
                format!("Cert={url_encoded}")
            })
            .collect::<Vec<_>>()
            .join(",");
        request
            .headers_mut()
            .insert(X_FORWARDED_CLIENT_CERT, HeaderValue::from_str(&xfcc)?);
    }

    let peer = Peer {
        client: client_ip,
        scheme: scheme.as_ref().to_owned(),
    };
    if is_websocket_upgrade(request.headers()) {
        return Ok(asgi.websocket(request, &peer).await?);
    }
    Ok(asgi.http(request, &peer).await?)
}

fn is_websocket_upgrade(headers: &HeaderMap<HeaderValue>) -> bool {
    let has_upgrade = headers
        .get(UPGRADE)
        .and_then(|v| v.to_str().ok())
        .is_some_and(|v| v.eq_ignore_ascii_case("websocket"));

    let has_connection = headers
        .get(CONNECTION)
        .and_then(|v| v.to_str().ok())
        .is_some_and(|v| {
            v.split(',')
                .any(|part| part.trim().eq_ignore_ascii_case("upgrade"))
        });

    let has_websocket_key = headers.contains_key(SEC_WEBSOCKET_KEY);
    let has_websocket_version = headers.contains_key(SEC_WEBSOCKET_VERSION);

    has_upgrade && has_connection && has_websocket_key && has_websocket_version
}

#[instrument(skip_all)]
async fn health_ready(State(server): State<Arc<Server>>) -> Result<StatusCode> {
    if !server.is_alive().await {
        warn!("server detected as not alive");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    if let Err(err) = sqlx::query("SELECT 1").execute(db::get()).await {
        warn!(?err, "failed to check db health");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    match server.health_ready().await {
        Ok(true) => {}
        Ok(false) => {
            warn!("server responded not ready");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
        Err(err) => {
            warn!(?err, "failed to check server health readiness");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
    }

    if let Some(workers) = server.workers.load_full() {
        if !workers.are_alive().await {
            warn!("workers detected as not alive");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }

        match workers.health_ready().await {
            Ok(true) => {}
            Ok(false) => {
                warn!("workers responded not ready");
                return Ok(StatusCode::SERVICE_UNAVAILABLE);
            }
            Err(err) => {
                warn!(?err, "failed to check workers health readiness");
                return Ok(StatusCode::SERVICE_UNAVAILABLE);
            }
        }
    }

    Ok(StatusCode::OK)
}

#[instrument(skip_all)]
async fn health_live(State(server): State<Arc<Server>>) -> Result<StatusCode> {
    if !server.is_alive().await {
        warn!("server detected as not alive");
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }

    if !server.health_live().await? {
        return Ok(StatusCode::SERVICE_UNAVAILABLE);
    }
    match server.health_live().await {
        Ok(true) => {}
        Ok(false) => {
            warn!("server responded not live");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
        Err(err) => {
            warn!(?err, "failed to check server health liveness");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }
    }

    if let Some(workers) = server.workers.load_full() {
        if !workers.are_alive().await {
            warn!("workers detected as not alive");
            return Ok(StatusCode::SERVICE_UNAVAILABLE);
        }

        match workers.health_live().await {
            Ok(true) => {}
            Ok(false) => {
                warn!("workers responded not live");
                return Ok(StatusCode::SERVICE_UNAVAILABLE);
            }
            Err(err) => {
                warn!(?err, "failed to check workers health liveness");
                return Ok(StatusCode::SERVICE_UNAVAILABLE);
            }
        }
    }

    Ok(StatusCode::OK)
}

pub(super) fn build_router(server: &Arc<Server>) -> eyre::Result<Router> {
    // Router for monitoring endpoints, under /-/
    let monitoring_router = wrap_router(
        Router::new()
            .route("/health/ready/", any(health_ready))
            .route("/health/live/", any(health_live))
            .fallback(any(StatusCode::NOT_FOUND))
            .with_state(Arc::clone(server)),
        true,
    );
    // Static files
    let static_router = wrap_router(super::r#static::build_router(), true);
    // Router for endpoints handled in Python
    let python_router = wrap_router(
        Router::new()
            .fallback(forward_request)
            .with_state(Arc::clone(server)),
        // Enable tracing but only in debug.
        config::get().debug,
    );

    let router = Router::new()
        .nest("/-/", monitoring_router.clone())
        .merge(static_router)
        .merge(python_router);

    let web_path = &config::get().web.path;
    let router = if web_path == "/" {
        router
    } else {
        let redirect_response = (
            StatusCode::FOUND,
            [(LOCATION, HeaderValue::from_str(web_path)?)],
        );
        let redirect_router = wrap_router(Router::new().route("/", any(redirect_response)), true);

        Router::new()
            .merge(redirect_router)
            .nest(web_path, router)
            .nest("/-/", monitoring_router)
    };

    Ok(router)
}

#[cfg(test)]
mod tests {
    use axum::http::Method;

    use super::is_django_http_method;

    #[test]
    fn django_http_methods_are_allowed() {
        for method in [
            Method::GET,
            Method::HEAD,
            Method::POST,
            Method::PUT,
            Method::PATCH,
            Method::DELETE,
            Method::OPTIONS,
            Method::TRACE,
        ] {
            assert!(is_django_http_method(&method));
        }
    }

    #[test]
    fn unsupported_http_methods_are_rejected() {
        assert!(!is_django_http_method(&Method::CONNECT));
        assert!(!is_django_http_method(
            &Method::from_bytes(b"PROPFIND").expect("method")
        ));
    }
}
