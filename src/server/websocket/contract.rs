//! Asks Python whether to accept a WebSocket connection, see
//! `authentik/root/websocket_internal.py`.
//!
//! Python stays the only place that authorizes connections. The handshake costs one request
//! to gunicorn; the connection itself then lives in Rust.

use std::{collections::BTreeMap, fmt::Write as _, net::IpAddr, time::Duration};

use axum::{
    body::Body,
    http::{
        HeaderMap, Method, Request, StatusCode,
        header::{CONTENT_TYPE, HOST},
    },
};
use eyre::{Result, eyre};
use http_body_util::{BodyExt as _, Limited};
use serde::{Deserialize, Serialize};
use tokio::{sync::Semaphore, time::timeout};

use crate::server::ServerClient;

const AUTHORIZE_URI: &str = "http://localhost:8000/-/internal/ws/authorize/";
/// Bounds the whole authorization, including waiting for a free slot.
const AUTHORIZE_TIMEOUT: Duration = Duration::from_secs(10);
/// How many handshakes may wait on Python at once, so a reconnect storm can't occupy every
/// gunicorn worker.
const MAX_CONCURRENT_AUTHORIZATIONS: usize = 32;
const MAX_RESPONSE_SIZE: usize = 64 * 1024;

/// Headers Python needs to authorize and log a handshake.
const FORWARDED_HEADERS: [&str; 2] = ["cookie", "user-agent"];

#[derive(Debug, Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
pub(super) enum Route {
    Client,
}

#[derive(Debug, Serialize)]
struct AuthorizeRequest<'a> {
    route: Route,
    path: &'a str,
    headers: BTreeMap<&'static str, String>,
}

/// Python's answer, `WebsocketAuthorization` in `authentik/root/websocket_internal.py`.
#[derive(Debug, Deserialize, PartialEq, Eq)]
pub(super) struct Authorization {
    pub(super) accept: bool,
    /// Channel layer groups to join, already hashed by Python.
    #[serde(default)]
    pub(super) groups: Vec<String>,
}

#[derive(Debug)]
pub(super) struct Contract {
    client: ServerClient,
    admission: Semaphore,
}

impl Contract {
    pub(super) fn new(client: ServerClient) -> Self {
        Self {
            client,
            admission: Semaphore::new(MAX_CONCURRENT_AUTHORIZATIONS),
        }
    }

    pub(super) async fn authorize(
        &self,
        route: Route,
        path: &str,
        headers: &HeaderMap,
        client_ip: IpAddr,
    ) -> Result<Authorization> {
        timeout(
            AUTHORIZE_TIMEOUT,
            self.authorize_inner(route, path, headers, client_ip),
        )
        .await
        .map_err(|_| eyre!("authorizing the WebSocket connection timed out"))?
    }

    async fn authorize_inner(
        &self,
        route: Route,
        path: &str,
        headers: &HeaderMap,
        client_ip: IpAddr,
    ) -> Result<Authorization> {
        let _permit = self.admission.acquire().await?;

        let mut forwarded = BTreeMap::new();
        for name in FORWARDED_HEADERS {
            if let Some(value) = headers.get(name) {
                forwarded.insert(name, decode_header_value(value.as_bytes()));
            }
        }
        // What the relay sends upstream, and what Channels logs as the remote address.
        forwarded.insert("x-forwarded-for", client_ip.to_string());

        let body = serde_json::to_vec(&AuthorizeRequest {
            route,
            path,
            headers: forwarded,
        })?;
        let request = Request::builder()
            .method(Method::POST)
            .uri(AUTHORIZE_URI)
            .header(HOST, "localhost")
            .header(CONTENT_TYPE, "application/json")
            .body(Body::from(body))?;
        let response = self.client.request(request).await?;
        let status = response.status();
        let body = Limited::new(response.into_body(), MAX_RESPONSE_SIZE)
            .collect()
            .await
            .map_err(|err| eyre!("failed to read authorization response: {err}"))?
            .to_bytes();
        if status != StatusCode::OK {
            return Err(eyre!("authorization failed with status {status}"));
        }
        Ok(serde_json::from_slice(&body)?)
    }
}

/// Decodes a header value like Python's `bytes.decode(errors="backslashreplace")`, which is how
/// `ChannelsLoggingMiddleware` logs the headers of connections Channels serves.
fn decode_header_value(value: &[u8]) -> String {
    let mut decoded = String::with_capacity(value.len());
    for chunk in value.utf8_chunks() {
        decoded.push_str(chunk.valid());
        for byte in chunk.invalid() {
            let _ = write!(decoded, "\\x{byte:02x}");
        }
    }
    decoded
}

#[cfg(test)]
pub(super) mod tests {
    use std::{
        path::{Path, PathBuf},
        sync::{Arc, Mutex},
    };

    use axum::http::{
        HeaderValue,
        header::{COOKIE, USER_AGENT},
    };
    use hyper_unix_socket::UnixSocketConnector;
    use hyper_util::{client::legacy::Client, rt::TokioExecutor};
    use serde_json::{Value, json};
    use tempfile::TempDir;
    use tokio::{
        io::{AsyncReadExt as _, AsyncWriteExt as _},
        net::UnixListener,
    };

    use super::*;

    pub(in super::super) fn client(socket_path: &Path) -> ServerClient {
        Client::builder(TokioExecutor::new())
            .set_host(false)
            .build(UnixSocketConnector::new(PathBuf::from(socket_path)))
    }

    /// Stands in for gunicorn: answers every authorization with `status` and `response`, and
    /// records the request bodies it received.
    pub(in super::super) fn spawn_python(
        socket_path: &Path,
        status: u16,
        response: &Value,
    ) -> Arc<Mutex<Vec<Value>>> {
        let listener = UnixListener::bind(socket_path).expect("failed to bind upstream socket");
        let requests = Arc::new(Mutex::new(Vec::new()));
        let recorded = Arc::clone(&requests);
        let response = response.to_string();

        tokio::spawn(async move {
            loop {
                let (mut stream, _) = listener.accept().await.expect("failed to accept");
                let recorded = Arc::clone(&recorded);
                let response = response.clone();
                tokio::spawn(async move {
                    let mut request = Vec::new();
                    let mut buf = [0_u8; 4096];
                    let (head_end, content_length) = loop {
                        let read = stream.read(&mut buf).await.expect("failed to read");
                        assert!(read > 0, "connection closed before the request ended");
                        request.extend_from_slice(&buf[..read]);
                        if let Some(end) = request.windows(4).position(|w| w == b"\r\n\r\n") {
                            let head = String::from_utf8_lossy(&request[..end]).to_lowercase();
                            let length = head
                                .lines()
                                .find_map(|line| line.strip_prefix("content-length:"))
                                .map_or(0, |value| value.trim().parse().expect("length"));
                            break (end + 4, length);
                        }
                    };
                    while request.len() < head_end + content_length {
                        let read = stream.read(&mut buf).await.expect("failed to read");
                        request.extend_from_slice(&buf[..read]);
                    }
                    let body: Value = serde_json::from_slice(&request[head_end..])
                        .expect("request body is not JSON");
                    recorded.lock().expect("poisoned").push(body);
                    let reply = format!(
                        "HTTP/1.1 {status} OK\r\ncontent-type: \
                         application/json\r\ncontent-length: {}\r\nconnection: \
                         close\r\n\r\n{response}",
                        response.len()
                    );
                    stream
                        .write_all(reply.as_bytes())
                        .await
                        .expect("failed to write response");
                });
            }
        });

        requests
    }

    fn handshake_headers() -> HeaderMap {
        let mut headers = HeaderMap::new();
        headers.insert(COOKIE, HeaderValue::from_static("authentik_session=abc"));
        headers.insert(
            USER_AGENT,
            HeaderValue::from_bytes(b"Mozilla/5.0 Meta\xa0AI").expect("header"),
        );
        headers.insert("authorization", HeaderValue::from_static("Bearer secret"));
        headers
    }

    #[tokio::test]
    async fn sends_handshake_and_parses_answer() {
        let dir = TempDir::new().expect("failed to create temp dir");
        let socket_path = dir.path().join("authentik.sock");
        let requests = spawn_python(
            &socket_path,
            200,
            &json!({"accept": true, "groups": ["group-hash"]}),
        );
        let contract = Contract::new(client(&socket_path));

        let authorization = contract
            .authorize(
                Route::Client,
                "/ws/client/",
                &handshake_headers(),
                "192.0.2.1".parse().expect("ip"),
            )
            .await
            .expect("authorization failed");

        assert_eq!(
            authorization,
            Authorization {
                accept: true,
                groups: vec!["group-hash".to_owned()],
            }
        );
        let requests = requests.lock().expect("poisoned");
        assert_eq!(
            requests.as_slice(),
            [json!({
                "route": "client",
                "path": "/ws/client/",
                "headers": {
                    "cookie": "authentik_session=abc",
                    "user-agent": "Mozilla/5.0 Meta\\xa0AI",
                    "x-forwarded-for": "192.0.2.1",
                },
            })],
            "only the headers Python needs are forwarded"
        );
    }

    #[tokio::test]
    async fn error_status_is_an_error() {
        let dir = TempDir::new().expect("failed to create temp dir");
        let socket_path = dir.path().join("authentik.sock");
        spawn_python(&socket_path, 500, &json!({}));
        let contract = Contract::new(client(&socket_path));

        let result = contract
            .authorize(
                Route::Client,
                "/ws/client/",
                &HeaderMap::new(),
                "192.0.2.1".parse().expect("ip"),
            )
            .await;

        let err = result.expect_err("an error status must fail the authorization");
        assert!(err.to_string().contains("500"), "{err}");
    }

    #[test]
    fn header_values_are_decoded_like_python() {
        assert_eq!(decode_header_value(b"plain"), "plain");
        assert_eq!(
            decode_header_value(b"Mozilla/5.0 Meta\xa0AI"),
            "Mozilla/5.0 Meta\\xa0AI"
        );
        assert_eq!(decode_header_value(b"\xff"), "\\xff");
        assert_eq!(decode_header_value("Ünï".as_bytes()), "Ünï");
    }
}
