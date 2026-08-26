use std::sync::{Arc, LazyLock, atomic::Ordering};

use ak_axum::{
    accept::tls::TlsState,
    error::Result,
    extract::{client_ip::ClientIp, host::Host, scheme::Scheme, trusted_proxy::TrustedProxy},
    router::wrap_router,
};
use ak_common::{config, db};
use axum::{
    Extension, Router,
    body::Body,
    extract::{OriginalUri, Request, State},
    http::{
        HeaderName, HeaderValue, Method, StatusCode, Uri,
        header::{ACCEPT, CONTENT_TYPE, HOST, LOCATION, RETRY_AFTER},
    },
    response::{IntoResponse as _, Response},
    routing::any,
};
use http_body_util::BodyExt as _;
use serde_json::json;
use tracing::{instrument, warn};

use crate::server::{
    GUNICORN_READY, Server,
    core::websockets::{handle_websocket_upgrade, is_websocket_upgrade},
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

    if !GUNICORN_READY.load(Ordering::Relaxed) {
        return Ok(startup_response(&accept_header));
    }
    if !is_django_http_method(request.method()) {
        return Ok((StatusCode::NOT_IMPLEMENTED, "Unsupported HTTP method.\n").into_response());
    }

    let uri = Uri::builder()
        .scheme("http")
        .authority("localhost:8000")
        .path_and_query(uri.path_and_query().map(|x| x.as_str()).unwrap_or_default())
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
        return handle_websocket_upgrade(request, &server.socket_path).await;
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
    let gunicorn_router = wrap_router(
        Router::new()
            .fallback(forward_request)
            .with_state(Arc::clone(server)),
        // Enable tracing but only in debug.
        config::get().debug,
    );

    let router = Router::new()
        .nest("/-/", monitoring_router.clone())
        .merge(static_router)
        .merge(gunicorn_router);

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

mod websockets {
    use std::path::Path;

    use ak_axum::error::{AppError, Result};
    use axum::{
        body::Body,
        extract::Request,
        http::{
            HeaderMap, HeaderValue, StatusCode,
            header::{
                CONNECTION, SEC_WEBSOCKET_ACCEPT, SEC_WEBSOCKET_EXTENSIONS, SEC_WEBSOCKET_KEY,
                SEC_WEBSOCKET_PROTOCOL, SEC_WEBSOCKET_VERSION, UPGRADE,
            },
        },
        response::{IntoResponse as _, Response},
    };
    use futures::{SinkExt as _, StreamExt as _};
    use hyper::upgrade::OnUpgrade;
    use hyper_util::rt::TokioIo;
    use tokio::{net::UnixStream, sync::mpsc};
    use tokio_tungstenite::{
        WebSocketStream, client_async,
        tungstenite::{
            Error as TungsteniteError, Message, handshake::derive_accept_key, protocol::Role,
        },
    };
    use tracing::{debug, trace, warn};

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
        mut request: Request,
        socket_path: &Path,
    ) -> Result<Response> {
        let Some(ws_key) = request
            .headers()
            .get(SEC_WEBSOCKET_KEY)
            .and_then(|key| key.to_str().ok())
        else {
            return Ok((StatusCode::BAD_REQUEST, "").into_response());
        };

        let ws_accept = derive_accept_key(ws_key.as_bytes());

        request.headers_mut().remove(SEC_WEBSOCKET_EXTENSIONS);

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

        let stream = UnixStream::connect(socket_path).await?;
        let (upstream_ws, upstream_response) = match client_async(ws_request, stream).await {
            Ok(upstream) => upstream,
            Err(TungsteniteError::Http(upstream_response)) => {
                return Ok((upstream_response.status(), "").into_response());
            }
            Err(err) => return Err(err.into()),
        };

        let mut response = Response::builder()
            .status(StatusCode::SWITCHING_PROTOCOLS)
            .header(UPGRADE, "websocket")
            .header(CONNECTION, "upgrade")
            .header(SEC_WEBSOCKET_ACCEPT, ws_accept);
        if let Some(selected) = upstream_response.headers().get(SEC_WEBSOCKET_PROTOCOL) {
            response = response.header(SEC_WEBSOCKET_PROTOCOL, selected);
        }
        let response = response.body(Body::empty())?;

        let client_upgrade = hyper::upgrade::on(&mut request);
        tokio::spawn(async move {
            if let Err(err) = handle_websocket_connection(client_upgrade, upstream_ws).await {
                warn!("WebSocket connection error: {}", err.0);
            }
        });

        Ok(response)
    }

    async fn handle_websocket_connection(
        client_upgrade: OnUpgrade,
        upstream_ws: WebSocketStream<UnixStream>,
    ) -> Result<()> {
        let client_ws = WebSocketStream::from_raw_socket(
            TokioIo::new(client_upgrade.await?),
            Role::Server,
            None,
        )
        .await;

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
                            let _ = close_tx.send(()).await;
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
                let _ = close_tx.send(()).await;
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
                            let _ = close_tx_upstream.send(()).await;
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
                let _ = close_tx_upstream.send(()).await;
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

    #[cfg(test)]
    mod tests {
        use std::time::Duration;

        use axum::http::header::HOST;
        use tempfile::TempDir;
        use tokio::{
            io::{AsyncReadExt as _, AsyncWriteExt as _},
            net::UnixListener,
            sync::oneshot,
            time::timeout,
        };
        use tokio_tungstenite::{
            accept_hdr_async,
            tungstenite::handshake::server::{
                ErrorResponse, Request as UpstreamRequest, Response as UpstreamResponse,
            },
        };

        use super::*;

        const WS_KEY: &str = "dGhlIHNhbXBsZSBub25jZQ==";

        /// Stands in for the ASGI application on `socket_path`, answering the
        /// handshake the way uvicorn's wsproto implementation does: it names the
        /// subprotocol the application selected, and accepts `permessage-deflate`
        /// whenever the handshake offers it.
        ///
        /// Resolves to the headers the upstream handshake was made with.
        fn spawn_upstream(
            socket_path: &Path,
            subprotocol: Option<&'static str>,
        ) -> oneshot::Receiver<HeaderMap> {
            let listener = UnixListener::bind(socket_path).expect("failed to bind upstream socket");
            let (headers_tx, headers_rx) = oneshot::channel();

            tokio::spawn(async move {
                let (stream, _) = listener.accept().await.expect("failed to accept");
                #[expect(
                    clippy::result_large_err,
                    reason = "the callback signature is dictated by tungstenite"
                )]
                let callback = |request: &UpstreamRequest, mut response: UpstreamResponse| {
                    let headers = request.headers().clone();
                    if let Some(subprotocol) = subprotocol {
                        response.headers_mut().insert(
                            SEC_WEBSOCKET_PROTOCOL,
                            HeaderValue::from_static(subprotocol),
                        );
                    }
                    if headers.contains_key(SEC_WEBSOCKET_EXTENSIONS) {
                        response.headers_mut().insert(
                            SEC_WEBSOCKET_EXTENSIONS,
                            HeaderValue::from_static("permessage-deflate"),
                        );
                    }
                    drop(headers_tx.send(headers));
                    Ok::<_, ErrorResponse>(response)
                };
                let _upstream = accept_hdr_async(stream, callback)
                    .await
                    .expect("upstream handshake failed");
                // Hold the connection open for the rest of the test.
                std::future::pending::<()>().await;
            });

            headers_rx
        }

        /// Rejects the handshake instead of upgrading, the way the application
        /// answers when a consumer denies the connection.
        fn spawn_rejecting_upstream(socket_path: &Path) {
            let listener = UnixListener::bind(socket_path).expect("failed to bind upstream socket");

            tokio::spawn(async move {
                let (mut stream, _) = listener.accept().await.expect("failed to accept");
                let mut request = Vec::new();
                let mut byte = [0_u8; 1];
                while !request.ends_with(b"\r\n\r\n") {
                    if stream.read(&mut byte).await.expect("failed to read") == 0 {
                        break;
                    }
                    request.extend_from_slice(&byte);
                }
                stream
                    .write_all(b"HTTP/1.1 403 Forbidden\r\ncontent-length: 0\r\n\r\n")
                    .await
                    .expect("failed to write rejection");
            });
        }

        fn client_request(subprotocol: Option<&str>, extensions: Option<&str>) -> Request {
            let mut builder = Request::builder()
                // `forward_request` rewrites the URI before handing the request over.
                .uri("http://localhost:8000/ws/rac/connection-token/")
                .header(HOST, "authentik.company")
                .header(UPGRADE, "websocket")
                .header(CONNECTION, "upgrade")
                .header(SEC_WEBSOCKET_KEY, WS_KEY)
                .header(SEC_WEBSOCKET_VERSION, "13");
            if let Some(subprotocol) = subprotocol {
                builder = builder.header(SEC_WEBSOCKET_PROTOCOL, subprotocol);
            }
            if let Some(extensions) = extensions {
                builder = builder.header(SEC_WEBSOCKET_EXTENSIONS, extensions);
            }
            builder
                .body(Body::empty())
                .expect("failed to build client request")
        }

        /// RAC is the only consumer that negotiates a subprotocol, and browsers
        /// fail a connection when they offered one and the 101 names none.
        #[tokio::test]
        async fn upgrade_echoes_upstream_subprotocol() {
            let dir = TempDir::new().expect("failed to create temp dir");
            let socket_path = dir.path().join("authentik.sock");
            let _upstream = spawn_upstream(&socket_path, Some("guacamole"));

            let response =
                handle_websocket_upgrade(client_request(Some("guacamole"), None), &socket_path)
                    .await
                    .expect("upgrade should succeed");

            assert_eq!(response.status(), StatusCode::SWITCHING_PROTOCOLS);
            assert_eq!(
                response.headers().get(SEC_WEBSOCKET_PROTOCOL),
                Some(&HeaderValue::from_static("guacamole")),
                "the 101 must name the subprotocol the application selected"
            );
        }

        /// The bridge relays frames unchanged and cannot decode a compressed one,
        /// so the client's extension offer must not reach the application.
        #[tokio::test]
        async fn upgrade_does_not_offer_extensions_upstream() {
            let dir = TempDir::new().expect("failed to create temp dir");
            let socket_path = dir.path().join("authentik.sock");
            let upstream = spawn_upstream(&socket_path, Some("guacamole"));

            let response = handle_websocket_upgrade(
                client_request(
                    Some("guacamole"),
                    Some("permessage-deflate; client_max_window_bits"),
                ),
                &socket_path,
            )
            .await
            .expect("upgrade should succeed");

            assert!(
                !response.headers().contains_key(SEC_WEBSOCKET_EXTENSIONS),
                "the 101 must not name an extension"
            );

            let upstream_headers = timeout(Duration::from_secs(5), upstream)
                .await
                .expect("upstream did not receive a handshake")
                .expect("upstream dropped the handshake");
            assert!(
                !upstream_headers.contains_key(SEC_WEBSOCKET_EXTENSIONS),
                "the upstream handshake must not offer extensions"
            );
        }

        /// Every other consumer accepts without a subprotocol; naming one the
        /// client did not ask for makes browsers drop the connection.
        #[tokio::test]
        async fn upgrade_without_subprotocol_names_none() {
            let dir = TempDir::new().expect("failed to create temp dir");
            let socket_path = dir.path().join("authentik.sock");
            let _upstream = spawn_upstream(&socket_path, None);

            let response = handle_websocket_upgrade(client_request(None, None), &socket_path)
                .await
                .expect("upgrade should succeed");

            assert_eq!(response.status(), StatusCode::SWITCHING_PROTOCOLS);
            assert!(
                !response.headers().contains_key(SEC_WEBSOCKET_PROTOCOL),
                "the 101 must not name a subprotocol that was not requested"
            );
        }

        /// An application that denies the connection must not be preceded by a
        /// 101 the client would have to tear down immediately.
        #[tokio::test]
        async fn upgrade_propagates_upstream_rejection() {
            let dir = TempDir::new().expect("failed to create temp dir");
            let socket_path = dir.path().join("authentik.sock");
            spawn_rejecting_upstream(&socket_path);

            let response =
                handle_websocket_upgrade(client_request(Some("guacamole"), None), &socket_path)
                    .await
                    .expect("upgrade should return a response");

            assert_eq!(response.status(), StatusCode::FORBIDDEN);
        }
    }
}
