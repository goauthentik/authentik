//! Direct RAC file transport. Django authorizes control; only this module sees bytes.

use std::{
    collections::HashMap,
    io,
    net::SocketAddr,
    sync::Arc,
    time::{SystemTime, UNIX_EPOCH},
};

use aws_lc_rs::{constant_time, hmac};
use axum::{
    Router,
    body::{Body, Bytes},
    extract::{
        Path, Request, State,
        ws::{Message, WebSocket, WebSocketUpgrade},
    },
    http::{
        HeaderMap, Method, StatusCode,
        header::{AUTHORIZATION, CONTENT_DISPOSITION, CONTENT_LENGTH, COOKIE, HOST},
    },
    response::{IntoResponse, Response},
    routing::get,
};
use futures::{SinkExt, StreamExt};
use http_body_util::BodyExt as _;
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::client::legacy::Client;
use serde::{Deserialize, Serialize};
use tokio::{
    sync::{Mutex, Notify, mpsc},
    time::{Duration, timeout},
};
use uuid::Uuid;

use super::Server;

const FRAME: usize = 256 * 1024;
const WINDOW: u64 = 512 * 1024;
const CHUNK: u64 = 4 * 1024 * 1024;

#[derive(Clone, Debug, Deserialize)]
struct Owner {
    instance: String,
    address: String,
}

#[derive(Clone, Debug, Deserialize)]
struct Grant {
    owner: Owner,
    direction: String,
    size: u64,
    filename: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct Control {
    #[serde(rename = "type")]
    kind: String,
    #[serde(default)]
    offset: u64,
    #[serde(default)]
    length: u64,
    #[serde(default)]
    bytes: u64,
}

struct Pipe {
    grant: Grant,
    outgoing: mpsc::Sender<Message>,
    incoming: Arc<Mutex<mpsc::Receiver<Message>>>,
    operation: Arc<Mutex<()>>,
    offset: Mutex<u64>,
}

pub(super) struct Bulk {
    client: Client<UnixSocketConnector<std::path::PathBuf>, Body>,
    instance: String,
    address: String,
    secret: String,
    pipes: Mutex<HashMap<Uuid, Arc<Pipe>>>,
    changed: Notify,
}

impl Bulk {
    pub(super) fn new(server: Arc<Server>) -> Result<(Arc<Self>, SocketAddr), String> {
        let listen = std::env::var("AUTHENTIK_RAC_BULK_LISTEN")
            .unwrap_or_else(|_| "127.0.0.1:9823".to_owned())
            .parse::<SocketAddr>()
            .map_err(|error| format!("invalid RAC bulk listener: {error}"))?;
        let address = std::env::var("AUTHENTIK_RAC_BULK_ADVERTISE")
            .unwrap_or_else(|_| format!("http://{listen}"));
        if !address.starts_with("http://")
            || address.contains('@')
            || address.contains('?')
            || address.contains('#')
        {
            return Err("RAC bulk advertised address must be a private HTTP origin".to_owned());
        }
        if !listen.ip().is_loopback() && std::env::var("AUTHENTIK_RAC_BULK_ADVERTISE").is_err() {
            return Err(
                "a reachable RAC bulk advertised address is required for a non-loopback listener"
                    .to_owned(),
            );
        }
        let secret = ak_common::config::get().secret_key.clone();
        if secret.is_empty() {
            return Err("RAC bulk requires a configured secret key".to_owned());
        }
        Ok((
            Arc::new(Self {
                client: server.client.clone(),
                instance: Uuid::new_v4().to_string(),
                address,
                secret,
                pipes: Mutex::new(HashMap::new()),
                changed: Notify::new(),
            }),
            listen,
        ))
    }

    fn signature(&self, message: &str) -> String {
        let key = hmac::Key::new(hmac::HMAC_SHA256, self.secret.as_bytes());
        hmac::sign(&key, message.as_bytes())
            .as_ref()
            .iter()
            .map(|byte| format!("{byte:02x}"))
            .collect()
    }

    fn timestamp() -> String {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
            .to_string()
    }

    async fn authorize(
        &self,
        id: Uuid,
        operation: &str,
        headers: &HeaderMap,
    ) -> Result<Grant, StatusCode> {
        let timestamp = Self::timestamp();
        let tenant = if operation == "outpost" {
            headers
                .get("x-rac-tenant")
                .and_then(|value| value.to_str().ok())
                .filter(|value| !value.is_empty())
                .ok_or(StatusCode::BAD_REQUEST)?
        } else {
            ""
        };
        let message = format!(
            "{id}:{operation}:{timestamp}:{}:{}:{tenant}",
            self.instance, self.address,
        );
        let method = if operation == "upload" {
            Method::POST
        } else {
            Method::GET
        };
        let uri = format!("http://localhost:8000/if/rac/bulk/{id}/authorize/");
        let host = headers
            .get(HOST)
            .cloned()
            .unwrap_or_else(|| axum::http::HeaderValue::from_static("localhost"));
        let mut builder = Request::builder()
            .method(method)
            .uri(uri)
            .header(HOST, host)
            .header("X-RAC-Time", timestamp)
            .header("X-RAC-Operation", operation)
            .header("X-RAC-Instance", &self.instance)
            .header("X-RAC-Address", &self.address)
            .header("X-RAC-Signature", self.signature(&message));
        if operation == "outpost" {
            builder = builder.header("X-RAC-Tenant", tenant);
        }
        for name in [
            COOKIE,
            AUTHORIZATION,
            axum::http::HeaderName::from_static("x-authentik-csrf"),
        ] {
            if let Some(value) = headers.get(&name) {
                builder = builder.header(name, value);
            }
        }
        let request = builder
            .body(Body::empty())
            .map_err(|_| StatusCode::BAD_REQUEST)?;
        let response = self
            .client
            .request(request)
            .await
            .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)?;
        if !response.status().is_success() {
            return Err(response.status());
        }
        let bytes = response
            .into_body()
            .collect()
            .await
            .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)?
            .to_bytes();
        serde_json::from_slice(&bytes).map_err(|_| StatusCode::SERVICE_UNAVAILABLE)
    }

    async fn wait_pipe(&self, id: Uuid) -> Result<Arc<Pipe>, StatusCode> {
        timeout(Duration::from_secs(10), async {
            loop {
                if let Some(pipe) = self.pipes.lock().await.get(&id).cloned() {
                    return pipe;
                }
                self.changed.notified().await;
            }
        })
        .await
        .map_err(|_| StatusCode::SERVICE_UNAVAILABLE)
    }

    fn proxy_signature(&self, id: Uuid, method: &Method, timestamp: &str, offset: &str) -> String {
        self.signature(&format!("{id}:{method}:{timestamp}:{offset}"))
    }

    async fn forward(&self, id: Uuid, owner: &Owner, request: Request) -> Response {
        let method = request.method().clone();
        let offset = request
            .headers()
            .get("x-rac-offset")
            .and_then(|x| x.to_str().ok())
            .unwrap_or("")
            .to_owned();
        let timestamp = Self::timestamp();
        let url = format!(
            "{}/internal/rac/bulk/{id}/",
            owner.address.trim_end_matches('/')
        );
        let mut builder = reqwest::Client::new()
            .request(method.clone(), url)
            .header("x-rac-proxy-time", &timestamp)
            .header(
                "x-rac-proxy-signature",
                self.proxy_signature(id, &method, &timestamp, &offset),
            );
        for name in ["x-rac-offset", "content-length"] {
            if let Some(value) = request.headers().get(name) {
                builder = builder.header(name, value);
            }
        }
        let response = match builder
            .body(reqwest::Body::wrap_stream(
                request.into_body().into_data_stream(),
            ))
            .send()
            .await
        {
            Ok(response) => response,
            Err(_) => return StatusCode::BAD_GATEWAY.into_response(),
        };
        let mut outgoing = Response::builder().status(response.status());
        for name in [
            CONTENT_LENGTH,
            CONTENT_DISPOSITION,
            axum::http::header::CACHE_CONTROL,
            axum::http::header::CONTENT_TYPE,
            axum::http::header::X_CONTENT_TYPE_OPTIONS,
        ] {
            if let Some(value) = response.headers().get(&name) {
                outgoing = outgoing.header(name, value);
            }
        }
        outgoing
            .body(Body::from_stream(response.bytes_stream()))
            .unwrap_or_else(|_| StatusCode::BAD_GATEWAY.into_response())
    }
}

pub(super) fn public_router(state: Arc<Bulk>) -> Router {
    Router::new()
        .route("/ws/rac/bulk/{id}/", get(outpost_socket))
        .route("/if/rac/bulk/{id}/", get(public_file).put(public_file))
        .with_state(state)
}

pub(super) fn internal_router(state: Arc<Bulk>) -> Router {
    Router::new()
        .route(
            "/internal/rac/bulk/{id}/",
            get(internal_file).put(internal_file),
        )
        .with_state(state)
}

async fn outpost_socket(
    State(state): State<Arc<Bulk>>,
    Path(raw): Path<String>,
    headers: HeaderMap,
    ws: WebSocketUpgrade,
) -> Response {
    let Ok(id) = Uuid::parse_str(&raw) else {
        return StatusCode::NOT_FOUND.into_response();
    };
    let Ok(grant) = state.authorize(id, "outpost", &headers).await else {
        return StatusCode::FORBIDDEN.into_response();
    };
    if grant.owner.instance != state.instance {
        return StatusCode::CONFLICT.into_response();
    }
    ws.max_message_size(FRAME)
        .on_upgrade(move |socket| run_socket(state, id, grant, socket))
        .into_response()
}

async fn run_socket(state: Arc<Bulk>, id: Uuid, grant: Grant, socket: WebSocket) {
    let (mut writer, mut reader) = socket.split();
    let (outgoing, mut send_queue) = mpsc::channel::<Message>(16);
    let (incoming, receive_queue) = mpsc::channel::<Message>(16);
    let pipe = Arc::new(Pipe {
        grant,
        outgoing,
        incoming: Arc::new(Mutex::new(receive_queue)),
        operation: Arc::new(Mutex::new(())),
        offset: Mutex::new(0),
    });
    {
        let mut pipes = state.pipes.lock().await;
        if pipes.contains_key(&id) {
            return;
        }
        pipes.insert(id, pipe);
    }
    state.changed.notify_waiters();
    loop {
        tokio::select! {
            outbound = send_queue.recv() => {
                let Some(outbound) = outbound else { break; };
                if writer.send(outbound).await.is_err() { break; }
            }
            inbound = reader.next() => {
                let Some(Ok(inbound)) = inbound else { break; };
                if matches!(&inbound, Message::Binary(bytes) if bytes.len() > FRAME) { break; }
                if incoming.send(inbound).await.is_err() { break; }
            }
        }
    }
    state.pipes.lock().await.remove(&id);
    state.changed.notify_waiters();
}

async fn public_file(
    State(state): State<Arc<Bulk>>,
    Path(raw): Path<String>,
    request: Request,
) -> Response {
    let Ok(id) = Uuid::parse_str(&raw) else {
        return StatusCode::NOT_FOUND.into_response();
    };
    let operation = if request.method() == Method::PUT {
        "upload"
    } else {
        "download"
    };
    let grant = match state.authorize(id, operation, request.headers()).await {
        Ok(grant) => grant,
        Err(status) => return status.into_response(),
    };
    if grant.direction != operation {
        return StatusCode::FORBIDDEN.into_response();
    }
    if grant.owner.instance != state.instance {
        return state.forward(id, &grant.owner, request).await;
    }
    local_file(&state, id, request).await
}

async fn internal_file(
    State(state): State<Arc<Bulk>>,
    Path(raw): Path<String>,
    request: Request,
) -> Response {
    let Ok(id) = Uuid::parse_str(&raw) else {
        return StatusCode::NOT_FOUND.into_response();
    };
    let timestamp = request
        .headers()
        .get("x-rac-proxy-time")
        .and_then(|x| x.to_str().ok())
        .unwrap_or("");
    let offset = request
        .headers()
        .get("x-rac-offset")
        .and_then(|x| x.to_str().ok())
        .unwrap_or("");
    let signature = request
        .headers()
        .get("x-rac-proxy-signature")
        .and_then(|x| x.to_str().ok())
        .unwrap_or("");
    let recent = timestamp
        .parse::<u64>()
        .ok()
        .is_some_and(|value| SelfTime::recent(value));
    if !recent
        || constant_time::verify_slices_are_equal(
            signature.as_bytes(),
            state
                .proxy_signature(id, request.method(), timestamp, offset)
                .as_bytes(),
        )
        .is_err()
    {
        return StatusCode::FORBIDDEN.into_response();
    }
    local_file(&state, id, request).await
}

struct SelfTime;
impl SelfTime {
    fn recent(value: u64) -> bool {
        Bulk::timestamp()
            .parse::<u64>()
            .unwrap_or(0)
            .abs_diff(value)
            <= 30
    }
}

async fn local_file(state: &Bulk, id: Uuid, request: Request) -> Response {
    let pipe = match state.wait_pipe(id).await {
        Ok(pipe) => pipe,
        Err(status) => return status.into_response(),
    };
    if request.method() == Method::PUT {
        if pipe.grant.direction != "upload" {
            return StatusCode::FORBIDDEN.into_response();
        }
        upload(pipe, request).await
    } else {
        if pipe.grant.direction != "download" {
            return StatusCode::FORBIDDEN.into_response();
        }
        download(pipe).await
    }
}

async fn send_control(pipe: &Pipe, control: Control) -> Result<(), StatusCode> {
    let json = serde_json::to_string(&control).map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;
    pipe.outgoing
        .send(Message::Text(json.into()))
        .await
        .map_err(|_| StatusCode::BAD_GATEWAY)
}

async fn next_control(receiver: &mut mpsc::Receiver<Message>) -> Result<Control, StatusCode> {
    let message = timeout(Duration::from_secs(60), receiver.recv())
        .await
        .map_err(|_| StatusCode::GATEWAY_TIMEOUT)?
        .ok_or(StatusCode::BAD_GATEWAY)?;
    let Message::Text(text) = message else {
        return Err(StatusCode::BAD_GATEWAY);
    };
    serde_json::from_str(&text).map_err(|_| StatusCode::BAD_GATEWAY)
}

struct AbortOnDrop {
    pipe: Arc<Pipe>,
    active: bool,
}
impl Drop for AbortOnDrop {
    fn drop(&mut self) {
        if self.active {
            let _ = self.pipe.outgoing.try_send(Message::Close(None));
        }
    }
}

async fn upload(pipe: Arc<Pipe>, request: Request) -> Response {
    let offset = request
        .headers()
        .get("x-rac-offset")
        .and_then(|x| x.to_str().ok())
        .and_then(|x| x.parse::<u64>().ok());
    let length = request
        .headers()
        .get(CONTENT_LENGTH)
        .and_then(|x| x.to_str().ok())
        .and_then(|x| x.parse::<u64>().ok());
    let (Some(offset), Some(length)) = (offset, length) else {
        return StatusCode::BAD_REQUEST.into_response();
    };
    let _operation = pipe.operation.lock().await;
    if *pipe.offset.lock().await != offset {
        return StatusCode::CONFLICT.into_response();
    }
    if length == 0
        || length > CHUNK
        || offset
            .checked_add(length)
            .is_none_or(|end| end > pipe.grant.size)
    {
        return StatusCode::PAYLOAD_TOO_LARGE.into_response();
    }
    if send_control(
        &pipe,
        Control {
            kind: "start".into(),
            offset,
            length,
            bytes: 0,
        },
    )
    .await
    .is_err()
    {
        return StatusCode::BAD_GATEWAY.into_response();
    }
    let mut abort = AbortOnDrop {
        pipe: Arc::clone(&pipe),
        active: true,
    };
    let mut receiver = pipe.incoming.lock().await;
    let Ok(initial) = next_control(&mut receiver).await else {
        return StatusCode::BAD_GATEWAY.into_response();
    };
    if initial.kind != "credit" || initial.bytes > WINDOW || initial.offset != offset {
        return StatusCode::BAD_GATEWAY.into_response();
    }
    let mut credit = initial.bytes;
    let mut sent = 0u64;
    let mut transmitted = 0u64;
    let mut acknowledged = offset;
    let mut body = request.into_body().into_data_stream();
    while let Some(block) = body.next().await {
        let Ok(block) = block else {
            return StatusCode::BAD_REQUEST.into_response();
        };
        for part in block.chunks(FRAME) {
            sent += part.len() as u64;
            if sent > length {
                return StatusCode::BAD_REQUEST.into_response();
            }
            while credit < part.len() as u64 {
                let Ok(frame) = next_control(&mut receiver).await else {
                    return StatusCode::BAD_GATEWAY.into_response();
                };
                if frame.kind != "credit"
                    || frame.bytes > WINDOW
                    || frame.offset < acknowledged
                    || frame.offset > offset + transmitted
                {
                    return StatusCode::BAD_GATEWAY.into_response();
                }
                credit = (credit + frame.bytes).min(WINDOW);
                acknowledged = acknowledged.max(frame.offset);
            }
            if pipe
                .outgoing
                .send(Message::Binary(Bytes::copy_from_slice(part)))
                .await
                .is_err()
            {
                return StatusCode::BAD_GATEWAY.into_response();
            }
            credit -= part.len() as u64;
            transmitted += part.len() as u64;
        }
    }
    if sent != length {
        return StatusCode::BAD_REQUEST.into_response();
    }
    while acknowledged < offset + length {
        let Ok(frame) = next_control(&mut receiver).await else {
            return StatusCode::BAD_GATEWAY.into_response();
        };
        if frame.kind != "credit" || frame.offset < acknowledged || frame.offset > offset + length {
            return StatusCode::BAD_GATEWAY.into_response();
        }
        acknowledged = acknowledged.max(frame.offset);
    }
    *pipe.offset.lock().await = offset + length;
    abort.active = false;
    StatusCode::NO_CONTENT.into_response()
}

struct DownloadState {
    pipe: Arc<Pipe>,
    receiver: tokio::sync::OwnedMutexGuard<mpsc::Receiver<Message>>,
    _operation: tokio::sync::OwnedMutexGuard<()>,
    remaining: u64,
    prior: usize,
    failed: bool,
}

impl Drop for DownloadState {
    fn drop(&mut self) {
        let _ = self.pipe.outgoing.try_send(Message::Close(None));
    }
}

async fn download(pipe: Arc<Pipe>) -> Response {
    let operation = pipe.operation.clone().lock_owned().await;
    let receiver = pipe.incoming.clone().lock_owned().await;
    if send_control(
        &pipe,
        Control {
            kind: "start".into(),
            offset: 0,
            length: 0,
            bytes: 0,
        },
    )
    .await
    .is_err()
        || send_control(
            &pipe,
            Control {
                kind: "credit".into(),
                offset: 0,
                length: 0,
                bytes: WINDOW,
            },
        )
        .await
        .is_err()
    {
        return StatusCode::BAD_GATEWAY.into_response();
    }
    let size = pipe.grant.size;
    let filename = content_disposition(&pipe.grant.filename);
    let state = DownloadState {
        pipe,
        receiver,
        _operation: operation,
        remaining: size,
        prior: 0,
        failed: false,
    };
    let stream = futures::stream::unfold(state, async |mut state| {
        if state.failed {
            return None;
        }
        if state.prior > 0 {
            if send_control(
                &state.pipe,
                Control {
                    kind: "credit".into(),
                    offset: 0,
                    length: 0,
                    bytes: state.prior as u64,
                },
            )
            .await
            .is_err()
            {
                state.failed = true;
                return Some((Err(io::Error::other("RAC download disconnected")), state));
            }
            state.prior = 0;
        }
        match timeout(Duration::from_secs(60), state.receiver.recv()).await {
            Ok(Some(Message::Binary(bytes)))
                if !bytes.is_empty()
                    && bytes.len() <= FRAME
                    && bytes.len() as u64 <= state.remaining =>
            {
                state.remaining -= bytes.len() as u64;
                state.prior = bytes.len();
                Some((Ok::<Bytes, io::Error>(bytes), state))
            }
            Ok(Some(Message::Text(text))) => {
                let frame: Result<Control, _> = serde_json::from_str(&text);
                if frame.is_ok_and(|frame| frame.kind == "complete" && state.remaining == 0) {
                    None
                } else {
                    state.failed = true;
                    Some((Err(io::Error::other("RAC download truncated")), state))
                }
            }
            _ => {
                state.failed = true;
                Some((Err(io::Error::other("RAC download interrupted")), state))
            }
        }
    });
    Response::builder()
        .status(StatusCode::OK)
        .header(CONTENT_LENGTH, size.to_string())
        .header(CONTENT_DISPOSITION, filename)
        .header("cache-control", "no-store")
        .header("x-content-type-options", "nosniff")
        .header("content-type", "application/octet-stream")
        .body(Body::from_stream(stream))
        .unwrap_or_else(|_| StatusCode::INTERNAL_SERVER_ERROR.into_response())
}

fn content_disposition(filename: &str) -> String {
    let fallback: String = filename
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() || matches!(character, '-' | '_' | '.') {
                character
            } else {
                '_'
            }
        })
        .collect();
    let encoded: String = filename
        .as_bytes()
        .iter()
        .map(|byte| {
            if byte.is_ascii_alphanumeric() || matches!(*byte, b'-' | b'_' | b'.' | b'~') {
                char::from(*byte).to_string()
            } else {
                format!("%{byte:02X}")
            }
        })
        .collect();
    format!("attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}")
}

#[cfg(test)]
mod tests {
    use hyper_util::rt::TokioExecutor;

    use super::*;

    #[test]
    fn download_filename_uses_ascii_fallback_and_utf8_encoding() {
        assert_eq!(
            content_disposition("报告 1.txt"),
            "attachment; filename=\"___1.txt\"; filename*=UTF-8''%E6%8A%A5%E5%91%8A%201.txt"
        );
    }

    fn bulk(address: String) -> Arc<Bulk> {
        Arc::new(Bulk {
            client: Client::builder(TokioExecutor::new()).build(UnixSocketConnector::new(
                std::path::PathBuf::from("/tmp/rac-bulk-test-unused.sock"),
            )),
            instance: Uuid::new_v4().to_string(),
            address,
            secret: "shared-test-secret".into(),
            pipes: Mutex::new(HashMap::new()),
            changed: Notify::new(),
        })
    }

    fn pipe(
        direction: &str,
        size: u64,
    ) -> (Arc<Pipe>, mpsc::Sender<Message>, mpsc::Receiver<Message>) {
        let (outgoing, sent) = mpsc::channel(16);
        let (received, incoming) = mpsc::channel(16);
        let pipe = Arc::new(Pipe {
            grant: Grant {
                owner: Owner {
                    instance: "owner".into(),
                    address: "http://localhost".into(),
                },
                direction: direction.into(),
                size,
                filename: "data.bin".into(),
            },
            outgoing,
            incoming: Arc::new(Mutex::new(incoming)),
            operation: Arc::new(Mutex::new(())),
            offset: Mutex::new(0),
        });
        (pipe, received, sent)
    }

    #[tokio::test]
    async fn upload_requires_the_expected_offset_and_credit() {
        let size = WINDOW + 4;
        let (pipe, received, mut sent) = pipe("upload", size);
        let conflict = Request::builder()
            .method(Method::PUT)
            .header("x-rac-offset", "2")
            .header(CONTENT_LENGTH, "4")
            .body(Body::from("data"))
            .unwrap();
        assert_eq!(
            upload(pipe.clone(), conflict).await.status(),
            StatusCode::CONFLICT
        );
        received
            .send(Message::Text(
                format!(r#"{{"type":"credit","bytes":{WINDOW}}}"#).into(),
            ))
            .await
            .unwrap();
        let request = Request::builder()
            .method(Method::PUT)
            .header("x-rac-offset", "0")
            .header(CONTENT_LENGTH, size.to_string())
            .body(Body::from(vec![b'd'; size as usize]))
            .unwrap();
        let task = tokio::spawn(upload(pipe.clone(), request));
        assert!(matches!(sent.recv().await, Some(Message::Text(_))));
        for _ in 0..WINDOW as usize / FRAME {
            assert!(
                matches!(sent.recv().await, Some(Message::Binary(bytes)) if bytes.len() == FRAME)
            );
        }
        assert!(
            timeout(Duration::from_millis(40), sent.recv())
                .await
                .is_err()
        );
        received
            .send(Message::Text(
                format!(r#"{{"type":"credit","bytes":4,"offset":{WINDOW}}}"#).into(),
            ))
            .await
            .unwrap();
        assert!(matches!(sent.recv().await, Some(Message::Binary(bytes)) if bytes == b"dddd"[..]));
        received
            .send(Message::Text(
                format!(r#"{{"type":"credit","bytes":4,"offset":{size}}}"#).into(),
            ))
            .await
            .unwrap();
        assert_eq!(task.await.unwrap().status(), StatusCode::NO_CONTENT);
        assert_eq!(*pipe.offset.lock().await, size);
    }

    #[tokio::test]
    async fn another_instance_streams_download_without_session_stickiness() {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = format!("http://{}", listener.local_addr().unwrap());
        let owner = bulk(address.clone());
        let entry = bulk("http://127.0.0.1:1".into());
        let id = Uuid::new_v4();
        let (pipe, received, mut sent) = pipe("download", 4);
        owner.pipes.lock().await.insert(id, pipe);
        let server = tokio::spawn(axum::serve(listener, internal_router(owner)).into_future());
        let forward = tokio::spawn({
            let entry = entry.clone();
            async move {
                entry
                    .forward(
                        id,
                        &Owner {
                            instance: "other".into(),
                            address,
                        },
                        Request::builder()
                            .method(Method::GET)
                            .body(Body::empty())
                            .unwrap(),
                    )
                    .await
            }
        });
        assert!(matches!(sent.recv().await, Some(Message::Text(_))));
        assert!(matches!(sent.recv().await, Some(Message::Text(_))));
        received
            .send(Message::Binary(Bytes::from_static(b"data")))
            .await
            .unwrap();
        received
            .send(Message::Text(r#"{"type":"complete"}"#.into()))
            .await
            .unwrap();
        let response = forward.await.unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()[CONTENT_LENGTH], "4");
        assert_eq!(
            response.into_body().collect().await.unwrap().to_bytes(),
            b"data"[..]
        );
        server.abort();
    }

    #[tokio::test]
    async fn another_instance_streams_upload_without_session_stickiness() {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = format!("http://{}", listener.local_addr().unwrap());
        let owner = bulk(address.clone());
        let entry = bulk("http://127.0.0.1:1".into());
        let id = Uuid::new_v4();
        let (pipe, received, mut sent) = pipe("upload", 4);
        owner.pipes.lock().await.insert(id, pipe);
        let server = tokio::spawn(axum::serve(listener, internal_router(owner)).into_future());
        let forward = tokio::spawn({
            let entry = entry.clone();
            async move {
                entry
                    .forward(
                        id,
                        &Owner {
                            instance: "other".into(),
                            address,
                        },
                        Request::builder()
                            .method(Method::PUT)
                            .header("x-rac-offset", "0")
                            .header(CONTENT_LENGTH, "4")
                            .body(Body::from("data"))
                            .unwrap(),
                    )
                    .await
            }
        });
        received
            .send(Message::Text(
                format!(r#"{{"type":"credit","bytes":{WINDOW}}}"#).into(),
            ))
            .await
            .unwrap();
        assert!(matches!(sent.recv().await, Some(Message::Text(_))));
        assert!(matches!(sent.recv().await, Some(Message::Binary(bytes)) if bytes == b"data"[..]));
        received
            .send(Message::Text(
                r#"{"type":"credit","bytes":4,"offset":4}"#.into(),
            ))
            .await
            .unwrap();
        assert_eq!(forward.await.unwrap().status(), StatusCode::NO_CONTENT);
        server.abort();
    }
}
