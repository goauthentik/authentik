use std::sync::{Arc, LazyLock, atomic::Ordering};

use axum::{
    Extension, Router,
    body::Body,
    extract::{Request, State},
    http::{
        HeaderName, HeaderValue, StatusCode, Uri,
        header::{ACCEPT, CONTENT_TYPE, HOST, RETRY_AFTER},
    },
    middleware::{Next, from_fn},
    response::{IntoResponse, Response},
    routing::any,
};
use http_body_util::BodyExt;
use serde_json::json;

use crate::{
    axum::{
        accept::tls::TlsState,
        error::Result,
        extract::{client_ip::ClientIp, host::Host, scheme::Scheme, trusted_proxy::TrustedProxy},
        router::wrap_router,
    },
    config, db,
    server::{
        GUNICORN_READY, Server,
        core::websockets::{handle_websocket_upgrade, is_websocket_upgrade},
    },
};

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

const SERVER: HeaderName = HeaderName::from_static("server");
const X_FORWARDED_CLIENT_CERT: HeaderName = HeaderName::from_static("x-forwarded-client-cert");
const X_FORWARDED_FOR: HeaderName = HeaderName::from_static("x-forwarded-for");
const X_FORWARDED_PROTO: HeaderName = HeaderName::from_static("x-forwarded-proto");
const X_POWERED_BY: HeaderName = HeaderName::from_static("x-powered-by");

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

async fn forward_request(
    ClientIp(client_ip): ClientIp,
    Host(host): Host,
    Scheme(scheme): Scheme,
    State(server): State<Arc<Server>>,
    TrustedProxy(trusted_proxy): TrustedProxy,
    tls_state: Option<Extension<TlsState>>,
    mut request: Request,
) -> Result<Response> {
    let accept_header = request
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
            request
                .uri()
                .path_and_query()
                .map(|x| x.as_str())
                .unwrap_or_default(),
        )
        .build()?;
    *request.uri_mut() = uri;

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

    if is_websocket_upgrade(request.headers()) {
        return handle_websocket_upgrade(request, server).await;
    }

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
            .insert("X_FORWARDED_CLIENT_CERT", HeaderValue::from_str(&xfcc)?);
    }

    match server.client.request(request).await {
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

fn build_gunicorn_router(server: Arc<Server>) -> Router {
    wrap_router(
        Router::new().fallback(forward_request).with_state(server),
        config::get().debug, // enable tracing only in debug mode
    )
}

async fn powered_by_middleware(request: Request, next: Next) -> Response {
    let mut response = next.run(request).await;
    response.headers_mut().remove(SERVER);
    response
        .headers_mut()
        .insert(X_POWERED_BY, HeaderValue::from_static("authentik"));
    response
}

async fn health_ready(State(server): State<Arc<Server>>) -> impl IntoResponse {
    #[expect(clippy::if_same_then_else, reason = "For easier reading")]
    if !server.is_alive().await {
        StatusCode::SERVICE_UNAVAILABLE
    } else if sqlx::query("SELECT 1").execute(db::get()).await.is_err() {
        StatusCode::SERVICE_UNAVAILABLE
    } else if let Some(workers) = server.workers.load_full()
        && !workers.are_alive().await
    {
        StatusCode::SERVICE_UNAVAILABLE
    } else {
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/ready/")
            .header(HOST, "localhost")
            .body(Body::from(""));
        if let Ok(req) = req
            && let Ok(res) = server.client.request(req).await
        {
            res.status()
        } else {
            StatusCode::SERVICE_UNAVAILABLE
        }
    }
}

// TODO: subpath
pub(super) fn build_router(server: Arc<Server>) -> Router {
    wrap_router(
        Router::new()
            .route("/-/metrics/", any((StatusCode::NOT_FOUND, "not found")))
            .route("/-/health/ready/", any(health_ready))
            .with_state(server.clone())
            .merge(super::r#static::build_router()),
        true,
    )
    .merge(build_gunicorn_router(server))
    .layer(from_fn(powered_by_middleware))
}

mod websockets {
    use std::sync::Arc;

    use axum::{
        body::Body,
        extract::Request,
        http::{
            HeaderMap, HeaderValue, StatusCode,
            header::{
                CONNECTION, SEC_WEBSOCKET_ACCEPT, SEC_WEBSOCKET_KEY, SEC_WEBSOCKET_VERSION, UPGRADE,
            },
        },
        response::{IntoResponse, Response},
    };
    use futures::{SinkExt, StreamExt};
    use hyper_util::rt::TokioIo;
    use tokio::{net::UnixStream, sync::mpsc};
    use tokio_tungstenite::{
        WebSocketStream, client_async,
        tungstenite::{Message, handshake::derive_accept_key, protocol::Role},
    };
    use tracing::{debug, trace, warn};

    use crate::{
        axum::error::{AppError, Result},
        server::Server,
    };

    pub(super) fn is_websocket_upgrade(headers: &HeaderMap<HeaderValue>) -> bool {
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

    pub(super) async fn handle_websocket_upgrade(
        request: Request,
        server: Arc<Server>,
    ) -> Result<Response> {
        let Some(ws_key) = request
            .headers()
            .get(SEC_WEBSOCKET_KEY)
            .and_then(|key| key.to_str().ok())
        else {
            return Ok((StatusCode::BAD_REQUEST, "").into_response());
        };

        let ws_accept = derive_accept_key(ws_key.as_bytes());

        let path_q = request
            .uri()
            .path_and_query()
            .map(|x| x.as_str())
            .unwrap_or_default();
        let uri = format!("ws://localhost:8000{path_q}");

        let mut ws_request =
            tokio_tungstenite::tungstenite::handshake::client::Request::builder().uri(uri);
        for (k, v) in request.headers() {
            ws_request = ws_request.header(k.as_str(), v);
        }
        let ws_request = ws_request.body(())?;

        let response = Response::builder()
            .status(StatusCode::SWITCHING_PROTOCOLS)
            .header(UPGRADE, "websocket")
            .header(CONNECTION, "upgrade")
            .header(SEC_WEBSOCKET_ACCEPT, ws_accept)
            .body(Body::empty())?;

        tokio::spawn(async move {
            if let Err(err) = handle_websocket_connection(request, server, ws_request).await {
                warn!("WebSocket connection error: {}", err.0);
            }
        });

        Ok(response)
    }

    async fn handle_websocket_connection(
        request: Request,
        server: Arc<Server>,
        ws_request: tokio_tungstenite::tungstenite::handshake::client::Request,
    ) -> Result<()> {
        let upgraded = hyper::upgrade::on(request).await?;
        let io = TokioIo::new(upgraded);
        let client_ws = WebSocketStream::from_raw_socket(io, Role::Server, None).await;

        let upstream_ws = {
            let stream = UnixStream::connect(&server.socket_path).await?;
            let (ws_stream, _) = client_async(ws_request, stream).await?;
            ws_stream
        };

        let (mut client_sender, mut client_receiver) = client_ws.split();
        let (mut upstream_sender, mut upstream_receiver) = upstream_ws.split();

        let (close_tx, mut close_rx) = mpsc::channel::<()>(1);
        let close_tx_upstream = close_tx.clone();

        let client_to_upstream = tokio::spawn(async move {
            let mut client_closed = false;
            while let Some(msg) = client_receiver.next().await {
                let msg = msg?;
                match msg {
                    Message::Close(_) => {
                        if !client_closed {
                            upstream_sender.send(Message::Close(None)).await?;
                            close_tx.send(()).await.ok();
                            client_closed = true;
                            break;
                        }
                    }
                    msg @ (Message::Binary(_)
                    | Message::Text(_)
                    | Message::Ping(_)
                    | Message::Pong(_)) => {
                        if !client_closed {
                            upstream_sender.send(msg).await?;
                        }
                    }
                    Message::Frame(_) => {}
                }
            }
            if !client_closed {
                upstream_sender.send(Message::Close(None)).await?;
                close_tx.send(()).await.ok();
            }
            Ok::<_, AppError>(())
        });

        let upstream_to_client = tokio::spawn(async move {
            let mut upstream_closed = false;
            while let Some(msg) = upstream_receiver.next().await {
                let msg = msg?;
                match msg {
                    Message::Close(_) => {
                        if !upstream_closed {
                            client_sender.send(Message::Close(None)).await?;
                            close_tx_upstream.send(()).await.ok();
                            upstream_closed = true;
                            break;
                        }
                    }
                    msg @ (Message::Binary(_)
                    | Message::Text(_)
                    | Message::Ping(_)
                    | Message::Pong(_)) => {
                        if !upstream_closed {
                            client_sender.send(msg).await?;
                        }
                    }
                    Message::Frame(_) => {}
                }
            }
            if !upstream_closed {
                client_sender.send(Message::Close(None)).await?;
                close_tx_upstream.send(()).await.ok();
            }
            Ok::<_, AppError>(())
        });

        tokio::select! {
            _ = close_rx.recv() => {
                trace!("WebSocket connection closed gracefully");
            },
            res = client_to_upstream => {
                if let Err(err) = res {
                    debug!("Client to upstream task failed: {:?}", err);
                }
            }
            res = upstream_to_client => {
                if let Err(err) = res {
                    debug!("Upstream to client task failed: {:?}", err);
                }
            }
        }

        Ok(())
    }
}
