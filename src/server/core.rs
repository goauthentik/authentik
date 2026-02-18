use axum::http::{
    HeaderValue,
    header::{ACCEPT, HOST},
};
use std::{
    path::PathBuf,
    sync::{LazyLock, atomic::Ordering},
    time::Duration,
};

use axum::{
    Extension, Router,
    body::Body,
    extract::{Request, State},
    http::{
        HeaderName, StatusCode, Uri,
        header::{CONTENT_TYPE, RETRY_AFTER},
    },
    response::Response,
};
use http_body_util::BodyExt;
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use serde_json::json;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::Level;

use crate::{
    axum::{
        accept::tls::TlsState,
        error::Result,
        extract::{client_ip::ClientIP, host::Host, scheme::Scheme},
    },
    config::get_config,
    server::gunicorn::GUNICORN_READY,
};

type BackendClient = Client<UnixSocketConnector<PathBuf>, Body>;

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
        .unwrap()
});

static STARTUP_RESPONSE_HTML: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/html")
        .body(include_str!("../../web/dist/standalone/loading/startup.html").to_owned())
        .unwrap()
});

static STARTUP_RESPONSE_PLAIN: LazyLock<Response<String>> = LazyLock::new(|| {
    Response::builder()
        .status(StatusCode::SERVICE_UNAVAILABLE)
        .header(CONTENT_TYPE, "text/plain")
        .body("authentik starting".to_owned())
        .unwrap()
});

const X_FORWARDED_FOR: HeaderName = HeaderName::from_static("x-forwarded-for");
const X_FORWARDED_PROTO: HeaderName = HeaderName::from_static("x-forwarded-proto");

const FORWARD_IGNORED_HEADERS: [HeaderName; 7] = [
    HeaderName::from_static("forwarded"),
    HeaderName::from_static("host"),
    X_FORWARDED_FOR,
    HeaderName::from_static("x-forwarded-host"),
    X_FORWARDED_PROTO,
    HeaderName::from_static("x-forwarded-scheme"),
    HeaderName::from_static("x-real-ip"),
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

async fn forward_request(
    ClientIP(client_ip): ClientIP,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(client): State<BackendClient>,
    _tls_state: Option<Extension<TlsState>>,
    mut req: Request,
) -> Result<Response> {
    // TODO: tls state
    let accept_header = req
        .headers()
        .get(ACCEPT)
        .map(|v| v.to_str().unwrap_or_default().to_owned())
        .unwrap_or_default();

    if !GUNICORN_READY.load(Ordering::Relaxed) {
        return Ok(startup_response(&accept_header));
    }

    let uri = Uri::builder()
        .scheme("http")
        .authority("localhost:8000")
        .path_and_query(
            req.uri()
                .path_and_query()
                .map(|x| x.as_str())
                .unwrap_or_default(),
        )
        .build()
        .unwrap();
    *req.uri_mut() = uri;

    for header_name in FORWARD_IGNORED_HEADERS {
        req.headers_mut().remove(header_name);
    }
    req.headers_mut().insert(
        X_FORWARDED_FOR,
        HeaderValue::from_str(&client_ip.to_string())?,
    );
    req.headers_mut()
        .insert(HOST, HeaderValue::from_str(&host)?);
    req.headers_mut()
        .insert(X_FORWARDED_PROTO, HeaderValue::from_str(scheme.as_ref())?);

    match client.request(req).await {
        Ok(res) => {
            let (parts, body) = res.into_parts();
            Ok(Response::from_parts(
                parts,
                Body::from_stream(body.into_data_stream()),
            ))
        }
        Err(_) => Ok(startup_response(&accept_header)),
    }
}

async fn build_proxy_router() -> Router {
    let connector = UnixSocketConnector::new(super::gunicorn::gunicorn_socket_path());
    let client = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .pool_max_idle_per_host(get_config().await.web.workers * get_config().await.web.threads)
        .set_host(false)
        .build(connector);

    Router::new().fallback(forward_request).with_state(client)
}

// TODO: subpath
pub(super) async fn build_router() -> Router {
    Router::new()
        .merge(super::r#static::build_router().await)
        .layer(
            // TODO: refine this, probably extract it to its own thing to be used with the proxy
            // outpost
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_request(DefaultOnRequest::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
        .merge(build_proxy_router().await)
}
