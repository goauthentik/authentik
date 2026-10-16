//! Hands connections to the ASGI application running in the embedded Python interpreter.

use std::{convert::Infallible, net::IpAddr, sync::Arc};

use axum::{
    body::{Body, Bytes},
    extract::Request,
    http::{
        HeaderMap, HeaderName, HeaderValue, StatusCode, Version,
        header::{
            CONNECTION, SEC_WEBSOCKET_ACCEPT, SEC_WEBSOCKET_KEY, SEC_WEBSOCKET_PROTOCOL, UPGRADE,
        },
    },
    response::{IntoResponse as _, Response},
};
use eyre::{Result, eyre};
use futures::{SinkExt as _, StreamExt as _};
use http_body_util::BodyExt as _;
use hyper::upgrade::OnUpgrade;
use hyper_util::rt::TokioIo;
use pyo3::{
    prelude::*,
    pybacked::{PyBackedBytes, PyBackedStr},
    types::{PyBytes, PyCFunction, PyDict, PyTuple},
};
use tokio::{
    sync::mpsc::{UnboundedReceiver, UnboundedSender, unbounded_channel},
    task::spawn_blocking,
};
use tokio_tungstenite::{
    WebSocketStream,
    tungstenite::{
        Message,
        handshake::derive_accept_key,
        protocol::{CloseFrame, Role},
    },
};
use tracing::{trace, warn};

/// A message the application sent.
#[derive(Debug)]
enum Sent {
    ResponseStart {
        status: u16,
        headers: HeaderMap,
    },
    ResponseBody {
        body: Bytes,
        more_body: bool,
    },
    WebsocketAccept {
        subprotocol: Option<String>,
        headers: HeaderMap,
    },
    WebsocketSend(Message),
    WebsocketClose(CloseFrame),
    /// The application returned.
    Done,
}

/// A message for the application to receive.
#[derive(Debug)]
enum Received {
    HttpRequest(Bytes),
    HttpDisconnect,
    WebsocketConnect,
    WebsocketReceive(Message),
    WebsocketDisconnect(u16),
}

fn extract_headers(message: &Bound<'_, PyDict>) -> PyResult<HeaderMap> {
    let mut headers = HeaderMap::new();
    let Some(items) = message.get_item("headers")? else {
        return Ok(headers);
    };
    for item in items.try_iter()? {
        let item = item?;
        let name: PyBackedBytes = item.get_item(0_i32)?.extract()?;
        let value: PyBackedBytes = item.get_item(1_i32)?.extract()?;
        if let (Ok(name), Ok(value)) = (
            HeaderName::from_bytes(&name),
            HeaderValue::from_bytes(&value),
        ) {
            headers.append(name, value);
        } else {
            warn!("ignoring invalid header from the application");
        }
    }
    Ok(headers)
}

/// The value at `key`, treating `None` like a missing key.
fn get<'py>(message: &Bound<'py, PyDict>, key: &str) -> PyResult<Option<Bound<'py, PyAny>>> {
    Ok(message.get_item(key)?.filter(|value| !value.is_none()))
}

fn extract_bytes(message: &Bound<'_, PyDict>, key: &str) -> PyResult<Option<Bytes>> {
    get(message, key)?
        .map(|value| Ok(Bytes::copy_from_slice(&value.extract::<PyBackedBytes>()?)))
        .transpose()
}

impl Sent {
    fn extract(message: &Bound<'_, PyAny>) -> PyResult<Option<Self>> {
        if message.is_none() {
            return Ok(Some(Self::Done));
        }
        let message = message.cast::<PyDict>()?;
        let Some(kind) = message.get_item("type")? else {
            return Ok(None);
        };
        Ok(match &*kind.extract::<PyBackedStr>()? {
            "http.response.start" => Some(Self::ResponseStart {
                status: get(message, "status")?.map_or(Ok(200), |v| v.extract())?,
                headers: extract_headers(message)?,
            }),
            "http.response.body" => Some(Self::ResponseBody {
                body: extract_bytes(message, "body")?.unwrap_or_default(),
                more_body: get(message, "more_body")?.map_or(Ok(false), |v| v.is_truthy())?,
            }),
            "websocket.accept" => Some(Self::WebsocketAccept {
                subprotocol: get(message, "subprotocol")?
                    .map(|v| v.extract())
                    .transpose()?,
                headers: extract_headers(message)?,
            }),
            "websocket.send" => match extract_bytes(message, "bytes")? {
                Some(bytes) => Some(Self::WebsocketSend(Message::Binary(bytes))),
                None => get(message, "text")?
                    .map(|v| v.extract::<String>())
                    .transpose()?
                    .map(|text| Self::WebsocketSend(Message::text(text))),
            },
            "websocket.close" => Some(Self::WebsocketClose(CloseFrame {
                code: get(message, "code")?
                    .map_or(Ok(1000_u16), |v| v.extract())?
                    .into(),
                reason: get(message, "reason")?
                    .map_or(Ok(String::new()), |v| v.extract())?
                    .into(),
            })),
            _ => None,
        })
    }
}

impl Received {
    fn into_dict(self, py: Python<'_>) -> PyResult<Bound<'_, PyDict>> {
        let dict = PyDict::new(py);
        match self {
            Self::HttpRequest(body) => {
                dict.set_item("type", "http.request")?;
                dict.set_item("body", PyBytes::new(py, &body))?;
                dict.set_item("more_body", false)?;
            }
            Self::HttpDisconnect => dict.set_item("type", "http.disconnect")?,
            Self::WebsocketConnect => dict.set_item("type", "websocket.connect")?,
            Self::WebsocketReceive(message) => {
                dict.set_item("type", "websocket.receive")?;
                match message {
                    Message::Text(text) => dict.set_item("text", text.as_str())?,
                    message => dict.set_item("bytes", PyBytes::new(py, &message.into_data()))?,
                }
            }
            Self::WebsocketDisconnect(code) => {
                dict.set_item("type", "websocket.disconnect")?;
                dict.set_item("code", code)?;
            }
        }
        Ok(dict)
    }
}

/// What the scope says about the connection, besides the request itself.
#[derive(Debug, Clone)]
pub(super) struct Peer {
    pub(super) client: IpAddr,
    /// `http` or `https`.
    pub(super) scheme: String,
}

fn build_scope<'py>(
    py: Python<'py>,
    request: &Head,
    peer: &Peer,
    websocket: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let scope = PyDict::new(py);
    let asgi = PyDict::new(py);
    asgi.set_item("version", "3.0")?;
    asgi.set_item("spec_version", "2.3")?;
    scope.set_item("asgi", asgi)?;
    let http_version = match request.version() {
        Version::HTTP_10 => "1.0",
        Version::HTTP_2 => "2",
        _ => "1.1",
    };
    scope.set_item("http_version", http_version)?;
    let raw_path = request.uri().path();
    scope.set_item(
        "path",
        percent_encoding::percent_decode_str(raw_path).decode_utf8_lossy(),
    )?;
    scope.set_item("raw_path", PyBytes::new(py, raw_path.as_bytes()))?;
    scope.set_item(
        "query_string",
        PyBytes::new(py, request.uri().query().unwrap_or_default().as_bytes()),
    )?;
    scope.set_item("root_path", "")?;
    let headers = request
        .headers()
        .iter()
        .map(|(name, value)| {
            PyTuple::new(
                py,
                [
                    PyBytes::new(py, name.as_str().as_bytes()),
                    PyBytes::new(py, value.as_bytes()),
                ],
            )
        })
        .collect::<PyResult<Vec<_>>>()?;
    scope.set_item("headers", headers)?;
    scope.set_item("client", (peer.client.to_string(), 0_u16))?;
    if websocket {
        scope.set_item("type", "websocket")?;
        let scheme = if peer.scheme == "https" { "wss" } else { "ws" };
        scope.set_item("scheme", scheme)?;
        let subprotocols: Vec<&str> = request
            .headers()
            .get_all(SEC_WEBSOCKET_PROTOCOL)
            .iter()
            .filter_map(|value| value.to_str().ok())
            .flat_map(|value| value.split(','))
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .collect();
        scope.set_item("subprotocols", subprotocols)?;
    } else {
        scope.set_item("type", "http")?;
        scope.set_item("scheme", &peer.scheme)?;
        scope.set_item("method", request.method().as_str())?;
    }
    Ok(scope)
}

/// The parts of a request the scope is made of.
type Head = axum::http::Request<()>;

fn head(request: &Request) -> Head {
    let mut head = Head::new(());
    *head.method_mut() = request.method().clone();
    *head.uri_mut() = request.uri().clone();
    *head.version_mut() = request.version();
    *head.headers_mut() = request.headers().clone();
    head
}

/// Hands the application the messages it receives, for one connection.
#[derive(Debug, Clone)]
struct Receiver(Arc<Py<PyAny>>);

impl Receiver {
    async fn push(&self, message: Received) -> Result<()> {
        let receive = Arc::clone(&self.0);
        spawn_blocking(move || {
            Python::attach(|py| {
                receive.call1(py, (message.into_dict(py)?,))?;
                Ok::<_, PyErr>(())
            })
        })
        .await??;
        Ok(())
    }
}

/// Tells the application the client is gone, once the response body is dropped.
struct DisconnectOnDrop(Receiver);

impl Drop for DisconnectOnDrop {
    fn drop(&mut self) {
        let receiver = self.0.clone();
        if let Ok(handle) = tokio::runtime::Handle::try_current() {
            handle.spawn(async move {
                if let Err(err) = receiver.push(Received::HttpDisconnect).await {
                    trace!(?err, "failed to notify the application of the disconnect");
                }
            });
        }
    }
}

/// The ASGI application in `lifecycle/server.py`.
#[derive(Debug)]
pub(crate) struct Asgi(Arc<Py<PyAny>>);

impl Asgi {
    /// Load authentik's application. Blocks for as long as Django takes to start.
    ///
    /// Returns the ASGI app, used for websockets, alongside the WSGI app `lifecycle.server`
    /// also builds, which handles ordinary HTTP requests (see `super::wsgi`). Both come out
    /// of this single call so Django's startup sequence only runs once.
    pub(super) fn load() -> Result<(Self, Py<PyAny>)> {
        Python::attach(|py| {
            let server = py.import("lifecycle.server")?.call_method0("load")?;
            let wsgi_application = server.getattr("wsgi_application")?.unbind();
            Ok::<_, PyErr>((Self::new(server.unbind()), wsgi_application))
        })
        .map_err(Into::into)
    }

    fn new(server: Py<PyAny>) -> Self {
        Self(Arc::new(server))
    }

    async fn call(&self, method: &'static str) -> Result<bool> {
        let server = Arc::clone(&self.0);
        Ok(spawn_blocking(move || {
            Python::attach(|py| server.call_method0(py, method)?.is_truthy(py))
        })
        .await??)
    }

    pub(super) async fn is_alive(&self) -> bool {
        self.call("is_alive").await.unwrap_or_else(|err| {
            warn!(?err, "failed to check if the application is alive");
            false
        })
    }

    pub(super) async fn shutdown(&self) -> Result<()> {
        self.call("shutdown").await.map(|_| ())
    }

    /// Start the application on a connection.
    async fn start(
        &self,
        head: Head,
        peer: &Peer,
        websocket: bool,
    ) -> Result<(Receiver, UnboundedReceiver<Sent>)> {
        let (tx, rx) = unbounded_channel::<Sent>();
        let server = Arc::clone(&self.0);
        let peer = peer.clone();
        let receive = spawn_blocking(move || {
            Python::attach(|py| {
                let scope = build_scope(py, &head, &peer, websocket)?;
                let send = send_function(py, tx)?;
                server.call_method1(py, "handle", (scope, send))
            })
        })
        .await??;
        Ok((Receiver(Arc::new(receive)), rx))
    }

    pub(super) async fn http(&self, request: Request, peer: &Peer) -> Result<Response> {
        let (receiver, mut rx) = self.start(head(&request), peer, false).await?;
        // ponytail: buffers the request body, which the body limit layer caps. Stream it to the
        // application if large uploads become a problem.
        let body = request.into_body().collect().await?.to_bytes();
        receiver.push(Received::HttpRequest(body)).await?;
        let guard = DisconnectOnDrop(receiver);

        let (status, headers) = loop {
            match rx.recv().await {
                Some(Sent::ResponseStart { status, headers }) => break (status, headers),
                Some(Sent::Done) | None => {
                    return Ok(StatusCode::INTERNAL_SERVER_ERROR.into_response());
                }
                Some(_) => {}
            }
        };

        // ponytail: the channel is unbounded, so a slow client makes a large streamed response
        // pile up in memory. Bound it once that matters.
        let body = futures::stream::unfold(Some((rx, guard)), async |state| {
            let (mut rx, guard) = state?;
            loop {
                match rx.recv().await {
                    Some(Sent::ResponseBody {
                        body,
                        more_body: true,
                    }) => return Some((Ok::<_, Infallible>(body), Some((rx, guard)))),
                    Some(Sent::ResponseBody {
                        body,
                        more_body: false,
                    }) => return Some((Ok(body), None)),
                    Some(Sent::Done) | None => return None,
                    Some(_) => {}
                }
            }
        });

        let mut response = Response::new(Body::from_stream(body));
        *response.status_mut() = StatusCode::from_u16(status)?;
        *response.headers_mut() = headers;
        Ok(response)
    }

    pub(super) async fn websocket(&self, mut request: Request, peer: &Peer) -> Result<Response> {
        let Some(ws_accept) = request
            .headers()
            .get(SEC_WEBSOCKET_KEY)
            .map(|key| derive_accept_key(key.as_bytes()))
        else {
            return Ok(StatusCode::BAD_REQUEST.into_response());
        };
        let client_upgrade = hyper::upgrade::on(&mut request);

        let (receiver, mut rx) = self.start(head(&request), peer, true).await?;
        receiver.push(Received::WebsocketConnect).await?;

        let (subprotocol, headers) = loop {
            match rx.recv().await {
                Some(Sent::WebsocketAccept {
                    subprotocol,
                    headers,
                }) => break (subprotocol, headers),
                Some(Sent::WebsocketClose(_) | Sent::Done) | None => {
                    return Ok(StatusCode::FORBIDDEN.into_response());
                }
                Some(_) => {}
            }
        };

        let mut response = Response::new(Body::empty());
        *response.status_mut() = StatusCode::SWITCHING_PROTOCOLS;
        *response.headers_mut() = headers;
        response
            .headers_mut()
            .insert(UPGRADE, HeaderValue::from_static("websocket"));
        response
            .headers_mut()
            .insert(CONNECTION, HeaderValue::from_static("upgrade"));
        response
            .headers_mut()
            .insert(SEC_WEBSOCKET_ACCEPT, HeaderValue::from_str(&ws_accept)?);
        if let Some(subprotocol) = subprotocol {
            response
                .headers_mut()
                .insert(SEC_WEBSOCKET_PROTOCOL, HeaderValue::from_str(&subprotocol)?);
        }

        tokio::spawn(async move {
            if let Err(err) = relay_websocket(client_upgrade, receiver, rx).await {
                warn!(?err, "websocket connection error");
            }
        });

        Ok(response)
    }
}

/// The function the application calls to send a message.
fn send_function(py: Python<'_>, tx: UnboundedSender<Sent>) -> PyResult<Bound<'_, PyCFunction>> {
    PyCFunction::new_closure(py, None, None, move |args, _kwargs| -> PyResult<()> {
        if let Some(message) = Sent::extract(&args.get_item(0)?)? {
            // The connection is already gone when nothing receives anymore
            let _ = tx.send(message);
        }
        Ok(())
    })
}

async fn relay_websocket(
    client_upgrade: OnUpgrade,
    receiver: Receiver,
    mut rx: UnboundedReceiver<Sent>,
) -> Result<()> {
    let client =
        WebSocketStream::from_raw_socket(TokioIo::new(client_upgrade.await?), Role::Server, None)
            .await;
    let (mut client_tx, mut client_rx) = client.split();

    // 1006: closed without a close frame
    let mut code = 1006_u16;
    let result = loop {
        tokio::select! {
            message = client_rx.next() => match message {
                Some(Ok(Message::Close(frame))) => {
                    code = frame.map_or(1005, |frame| frame.code.into());
                    break Ok(());
                }
                Some(Ok(message @ (Message::Text(_) | Message::Binary(_)))) => {
                    if let Err(err) = receiver.push(Received::WebsocketReceive(message)).await {
                        break Err(err);
                    }
                }
                // tungstenite answers pings itself
                Some(Ok(Message::Ping(_) | Message::Pong(_) | Message::Frame(_))) => {}
                Some(Err(err)) => break Err(err.into()),
                None => break Ok(()),
            },
            sent = rx.recv() => match sent {
                Some(Sent::WebsocketSend(message)) => {
                    if let Err(err) = client_tx.send(message).await {
                        break Err(err.into());
                    }
                }
                Some(Sent::WebsocketClose(frame)) => {
                    code = frame.code.into();
                    break client_tx.send(Message::Close(Some(frame))).await.map_err(Into::into);
                }
                Some(Sent::Done) | None => {
                    break client_tx.send(Message::Close(None)).await.map_err(Into::into);
                }
                Some(_) => {}
            },
        }
    };
    receiver.push(Received::WebsocketDisconnect(code)).await?;
    result.map_err(|err: eyre::Report| eyre!("websocket relay failed: {err}"))
}

#[cfg(test)]
mod tests {
    use std::{ffi::CString, net::Ipv4Addr};

    use axum::http::header::{HOST, SEC_WEBSOCKET_VERSION};

    use super::*;

    const APP: &str = r#"
import asyncio
from lifecycle.server import Server

async def app(scope, receive, send):
    if scope["type"] == "websocket":
        await receive()
        if scope["path"] == "/ws/deny/":
            await send({"type": "websocket.close"})
            return
        await send({"type": "websocket.accept", "subprotocol": (scope["subprotocols"] or [None])[0]})
        return
    message = await receive()
    await send({
        "type": "http.response.start",
        "status": 201,
        "headers": [(b"x-method", scope["method"].encode()), (b"x-client", scope["client"][0].encode())],
    })
    await send({"type": "http.response.body", "body": scope["path"].encode() + b"|", "more_body": True})
    await send({"type": "http.response.body", "body": message["body"]})

server = Server(app, asyncio.new_event_loop())
"#;

    fn asgi() -> Asgi {
        crate::python::initialize().expect("failed to initialize Python");
        Asgi::new(Python::attach(|py| {
            let cwd = std::env::current_dir().expect("no working directory");
            py.import("sys")
                .and_then(|sys| sys.getattr("path"))
                .and_then(|path| path.call_method1("insert", (0_i32, cwd.as_os_str())))
                .expect("failed to set sys.path");
            let code = CString::new(APP).expect("invalid code");
            PyModule::from_code(py, &code, c"test_app.py", c"test_app")
                .and_then(|module| module.getattr("server"))
                .expect("failed to load the test application")
                .unbind()
        }))
    }

    fn peer() -> Peer {
        Peer {
            client: IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1)),
            scheme: "https".to_owned(),
        }
    }

    fn websocket_request(path: &str, subprotocol: Option<&str>) -> Request {
        let mut builder = Request::builder()
            .uri(path)
            .header(HOST, "authentik.company")
            .header(UPGRADE, "websocket")
            .header(CONNECTION, "upgrade")
            .header(SEC_WEBSOCKET_KEY, "dGhlIHNhbXBsZSBub25jZQ==")
            .header(SEC_WEBSOCKET_VERSION, "13");
        if let Some(subprotocol) = subprotocol {
            builder = builder.header(SEC_WEBSOCKET_PROTOCOL, subprotocol);
        }
        builder
            .body(Body::empty())
            .expect("failed to build request")
    }

    #[tokio::test]
    async fn http_request_round_trips() {
        let request = Request::builder()
            .method("POST")
            .uri("/api/v3/caf%C3%A9/?a=b")
            .body(Body::from("hello"))
            .expect("failed to build request");

        let response = asgi().http(request, &peer()).await.expect("request failed");

        assert_eq!(response.status(), StatusCode::CREATED);
        assert_eq!(response.headers()["x-method"], "POST");
        assert_eq!(response.headers()["x-client"], "192.0.2.1");
        let body = response
            .into_body()
            .collect()
            .await
            .expect("failed to read body")
            .to_bytes();
        assert_eq!(body, "/api/v3/café/|hello");
    }

    /// RAC is the only consumer that negotiates a subprotocol, and browsers
    /// fail a connection when they offered one and the 101 names none.
    #[tokio::test]
    async fn websocket_upgrade_names_the_selected_subprotocol() {
        let response = asgi()
            .websocket(websocket_request("/ws/rac/", Some("guacamole")), &peer())
            .await
            .expect("upgrade failed");

        assert_eq!(response.status(), StatusCode::SWITCHING_PROTOCOLS);
        assert_eq!(response.headers()[SEC_WEBSOCKET_PROTOCOL], "guacamole");
    }

    #[tokio::test]
    async fn websocket_upgrade_without_subprotocol_names_none() {
        let response = asgi()
            .websocket(websocket_request("/ws/client/", None), &peer())
            .await
            .expect("upgrade failed");

        assert_eq!(response.status(), StatusCode::SWITCHING_PROTOCOLS);
        assert!(!response.headers().contains_key(SEC_WEBSOCKET_PROTOCOL));
    }

    /// An application that denies the connection must not be preceded by a
    /// 101 the client would have to tear down immediately.
    #[tokio::test]
    async fn websocket_denial_is_forbidden() {
        let response = asgi()
            .websocket(websocket_request("/ws/deny/", None), &peer())
            .await
            .expect("upgrade failed");

        assert_eq!(response.status(), StatusCode::FORBIDDEN);
    }
}
