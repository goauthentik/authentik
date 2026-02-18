use std::{sync::atomic::Ordering, time::Duration};

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
        extract::{client_ip::ClientIP, host::Host, scheme::Scheme},
    },
    config::get_config,
    server::gunicorn::GUNICORN_READY,
};

#[derive(Clone, Debug)]
struct CoreRouterState {
    client: Client<UnixSocketConnector<std::path::PathBuf>, Body>,
}

fn startup_response(accept: &str) -> Response {
    let mut response = Response::builder();
    response = response.status(StatusCode::SERVICE_UNAVAILABLE);

    if accept.contains("application/json") {
        response = response.header(RETRY_AFTER, "5");
        response = response.header(CONTENT_TYPE, "application/json");
        response
            .body(
                json!({
                    "error": "authentik starting",
                })
                .to_string()
                .into(),
            )
            .unwrap()
    } else if accept.contains("text/html") {
        response = response.header(CONTENT_TYPE, "text/html");
        response
            .body(include_str!("../../web/dist/standalone/loading/startup.html").into())
            .unwrap()
    } else {
        response = response.header(CONTENT_TYPE, "text/plain");
        response.body("authentik starting".into()).unwrap()
    }
}

async fn forward_request(
    ClientIP(client_ip): ClientIP,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(state): State<CoreRouterState>,
    _tls_state: Option<Extension<TlsState>>,
    req: Request,
) -> Response {
    // TODO: tls state
    let accept = req
        .headers()
        .get("accept")
        .map(|v| v.to_str().unwrap_or(""))
        .unwrap_or("")
        .to_owned();

    if !GUNICORN_READY.load(Ordering::Relaxed) {
        return startup_response(&accept);
    }

    let path_q = req.uri().path_and_query().map(|x| x.as_str()).unwrap_or("");

    let uri = Uri::builder()
        .scheme("http")
        .authority("localhost:8000")
        .path_and_query(path_q)
        .build()
        .unwrap();

    let forward_req = {
        let mut builder = Request::builder().method(req.method().clone()).uri(uri);

        let ignore_headers = &[
            HeaderName::from_static("forwarded"),
            HeaderName::from_static("host"),
            HeaderName::from_static("x-forwarded-for"),
            HeaderName::from_static("x-forwarded-host"),
            HeaderName::from_static("x-forwarded-proto"),
            HeaderName::from_static("x-forwarded-scheme"),
            HeaderName::from_static("x-real-ip"),
        ];

        for (key, value) in req.headers() {
            if !ignore_headers.contains(key) {
                builder = builder.header(key, value);
            }
        }
        builder = builder.header("X-Forwarded-For", client_ip.to_string());
        builder = builder.header("Host", host);
        builder = builder.header("X-Forwarded-Proto", scheme.to_string());

        let (_, body) = req.into_parts();
        builder.body(body).unwrap()
    };

    match state.client.request(forward_req).await {
        Ok(res) => {
            let (parts, body) = res.into_parts();
            let body = Body::from_stream(body.into_data_stream());

            let mut response = Response::new(body);
            *response.status_mut() = parts.status;
            *response.version_mut() = parts.version;
            *response.headers_mut() = parts.headers;
            response
        }
        Err(_) => startup_response(&accept),
    }
}

async fn build_proxy_router() -> Router {
    let connector = UnixSocketConnector::new(super::gunicorn::gunicorn_socket_path());
    let client = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .pool_max_idle_per_host(get_config().await.web.workers * get_config().await.web.threads)
        .set_host(false)
        .build(connector);

    let state = CoreRouterState { client };

    Router::new().fallback(forward_request).with_state(state)
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
