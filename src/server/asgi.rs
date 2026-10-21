//! Hands connections to the ASGI application running in the embedded Python interpreter.

use std::{net::IpAddr, sync::Arc};

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
use tracing::warn;

/// A message the application sent.
#[derive(Debug)]
enum Sent {
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
    Connect,
    Receive(Message),
    Disconnect(u16),
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
            Self::Connect => dict.set_item("type", "websocket.connect")?,
            Self::Receive(message) => {
                dict.set_item("type", "websocket.receive")?;
                match message {
                    Message::Text(text) => dict.set_item("text", text.as_str())?,
                    message => dict.set_item("bytes", PyBytes::new(py, &message.into_data()))?,
                }
            }
            Self::Disconnect(code) => {
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

fn build_scope<'py>(py: Python<'py>, request: &Head, peer: &Peer) -> PyResult<Bound<'py, PyDict>> {
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

/// The ASGI application in `lifecycle/server.py`.
#[derive(Debug)]
pub(crate) struct Asgi(Arc<Py<PyAny>>);

impl Asgi {
    /// Start authentik's application in a process forked after `lifecycle.server.preload`.
    ///
    /// Returns the ASGI app, used for websockets, alongside the WSGI app, which handles
    /// ordinary HTTP requests (see `super::wsgi`).
    pub(super) fn start_worker(worker_id: usize) -> Result<(Self, Py<PyAny>)> {
        Python::attach(|py| {
            let server = py
                .import("lifecycle.server")?
                .call_method1("post_fork", (worker_id,))?;
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
    async fn start(&self, head: Head, peer: &Peer) -> Result<(Receiver, UnboundedReceiver<Sent>)> {
        let (tx, rx) = unbounded_channel::<Sent>();
        let server = Arc::clone(&self.0);
        let peer = peer.clone();
        let receive = spawn_blocking(move || {
            Python::attach(|py| {
                let scope = build_scope(py, &head, &peer)?;
                let send = send_function(py, tx)?;
                server.call_method1(py, "handle", (scope, send))
            })
        })
        .await??;
        Ok((Receiver(Arc::new(receive)), rx))
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

        let (receiver, mut rx) = self.start(head(&request), peer).await?;
        receiver.push(Received::Connect).await?;

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
                    if let Err(err) = receiver.push(Received::Receive(message)).await {
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
    receiver.push(Received::Disconnect(code)).await?;
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

server = Server(app, asyncio.new_event_loop())
"#;

    fn asgi() -> Asgi {
        crate::python::initialize().expect("failed to initialize Python");
        Asgi::new(Python::attach(|py| {
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
