//! Hands ordinary HTTP requests to the Django WSGI application in the embedded interpreter.
//!
//! Unlike the ASGI bridge, this runs every request as a single blocking Python call on one of
//! a fixed set of threads that stay attached to the interpreter. On a free-threaded
//! interpreter that means requests genuinely run in parallel across OS threads, instead of
//! all funnelling through the one asyncio loop thread (and asgiref's single-worker
//! thread-sensitive executor) that the ASGI path is stuck with for synchronous Django/DRF code.

use std::{
    collections::HashMap,
    num::NonZeroUsize,
    sync::{Arc, Mutex, PoisonError, mpsc},
    thread,
};

use axum::{
    body::{Body, Bytes},
    extract::Request,
    http::{
        HeaderMap, HeaderName, HeaderValue, StatusCode, Version,
        header::{CONTENT_LENGTH, CONTENT_TYPE, HOST},
        request::Parts,
    },
    response::Response,
};
use eyre::{Result, eyre};
use http_body_util::BodyExt as _;
use pyo3::{
    exceptions::PyRuntimeError,
    prelude::*,
    pybacked::{PyBackedBytes, PyBackedStr},
    sync::PyOnceLock,
    types::{PyBytes, PyCFunction, PyDict},
};
use tokio::sync::oneshot;

use super::asgi::Peer;

type Job = Box<dyn FnOnce(Python<'_>) + Send>;

/// Threads that stay attached to the interpreter between requests.
///
/// Attaching a thread that has no Python thread state creates one, and detaching deletes it
/// again, along with everything in its `threading.local`s, like Django's per-thread state.
/// Threads from tokio's blocking pool would do that on every request, these keep theirs.
#[derive(Debug)]
struct Threads(mpsc::Sender<Job>);

impl Threads {
    fn new(count: NonZeroUsize) -> Result<Self> {
        let (tx, rx) = mpsc::channel::<Job>();
        let rx = Arc::new(Mutex::new(rx));
        for i in 0..count.get() {
            let rx = Arc::clone(&rx);
            thread::Builder::new()
                .name(format!("python-{i}"))
                .spawn(move || {
                    Python::attach(|py| {
                        // Only detached while waiting, so the thread state survives
                        while let Ok(job) =
                            py.detach(|| rx.lock().unwrap_or_else(PoisonError::into_inner).recv())
                        {
                            job(py);
                        }
                    });
                })?;
        }
        Ok(Self(tx))
    }

    async fn run<T, F>(&self, f: F) -> Result<T>
    where
        T: Send + 'static,
        F: FnOnce(Python<'_>) -> T + Send + 'static,
    {
        let (tx, rx) = oneshot::channel();
        self.0
            .send(Box::new(move |py| {
                let _ = tx.send(f(py));
            }))
            .map_err(|_| eyre!("the Python threads are gone"))?;
        Ok(rx.await?)
    }
}

/// The Django WSGI application in `authentik.root.wsgi`.
#[derive(Debug)]
pub(crate) struct Wsgi {
    application: Arc<Py<PyAny>>,
    threads: Threads,
}

static BYTES_IO: PyOnceLock<Py<PyAny>> = PyOnceLock::new();
static STDERR: PyOnceLock<Py<PyAny>> = PyOnceLock::new();

/// What `start_response` was called with.
type StartResponse = Arc<Mutex<Option<(u16, HeaderMap)>>>;

fn header_env_name(name: &HeaderName) -> String {
    let mut env = String::with_capacity(5 + name.as_str().len());
    env.push_str("HTTP_");
    for ch in name.as_str().chars() {
        env.push(if ch == '-' {
            '_'
        } else {
            ch.to_ascii_uppercase()
        });
    }
    env
}

/// Builds the WSGI `environ` dict for a request, with its body already buffered
/// (WSGI's `wsgi.input` is a blocking file-like object, which doesn't fit this request
/// being driven by an async runtime; the request body limit layer caps how big that buffer
/// can get).
fn build_environ<'py>(
    py: Python<'py>,
    parts: &Parts,
    body: &[u8],
    peer: &Peer,
) -> PyResult<Bound<'py, PyDict>> {
    let environ = PyDict::new(py);
    environ.set_item("REQUEST_METHOD", parts.method.as_str())?;
    environ.set_item(
        "PATH_INFO",
        percent_encoding::percent_decode_str(parts.uri.path()).decode_utf8_lossy(),
    )?;
    environ.set_item("SCRIPT_NAME", "")?;
    environ.set_item("QUERY_STRING", parts.uri.query().unwrap_or_default())?;
    environ.set_item(
        "SERVER_PROTOCOL",
        match parts.version {
            Version::HTTP_10 => "HTTP/1.0",
            Version::HTTP_2 => "HTTP/2.0",
            _ => "HTTP/1.1",
        },
    )?;
    environ.set_item("CONTENT_LENGTH", body.len().to_string())?;

    let host = parts
        .headers
        .get(HOST)
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default();
    let (server_name, server_port) = host
        .rsplit_once(':')
        .unwrap_or((host, if peer.scheme == "https" { "443" } else { "80" }));
    environ.set_item("SERVER_NAME", server_name)?;
    environ.set_item("SERVER_PORT", server_port)?;
    environ.set_item("REMOTE_ADDR", peer.client.to_string())?;

    environ.set_item("wsgi.version", (1_i32, 0_i32))?;
    environ.set_item("wsgi.url_scheme", peer.scheme.as_str())?;
    environ.set_item(
        "wsgi.input",
        BYTES_IO
            .import(py, "io", "BytesIO")?
            .call1((PyBytes::new(py, body),))?,
    )?;
    environ.set_item("wsgi.errors", STDERR.import(py, "sys", "stderr")?)?;
    environ.set_item("wsgi.multithread", true)?;
    environ.set_item("wsgi.multiprocess", false)?;
    environ.set_item("wsgi.run_once", false)?;

    // Headers repeated on the wire become one comma-joined HTTP_* value, per the WSGI spec.
    let mut grouped: HashMap<String, Vec<&str>> = HashMap::new();
    for (name, value) in &parts.headers {
        let Ok(value) = value.to_str() else {
            continue;
        };
        if name == CONTENT_TYPE {
            environ.set_item("CONTENT_TYPE", value)?;
            continue;
        }
        if name == CONTENT_LENGTH {
            // Already set from the buffered body above.
            continue;
        }
        grouped
            .entry(header_env_name(name))
            .or_default()
            .push(value);
    }
    for (name, values) in grouped {
        environ.set_item(name, values.join(", "))?;
    }

    Ok(environ)
}

/// The `start_response(status, headers)` callable the application calls before returning
/// its body iterable.
fn start_response_function(
    py: Python<'_>,
    captured: StartResponse,
) -> PyResult<Bound<'_, PyCFunction>> {
    PyCFunction::new_closure(py, None, None, move |args, _kwargs| -> PyResult<()> {
        let status_line: PyBackedStr = args.get_item(0_usize)?.extract()?;
        let status = status_line
            .split_ascii_whitespace()
            .next()
            .and_then(|code| code.parse().ok())
            .unwrap_or(500_u16);

        let mut headers = HeaderMap::new();
        for item in args.get_item(1_usize)?.try_iter()? {
            let item = item?;
            let name: PyBackedStr = item.get_item(0_i32)?.extract()?;
            let value: PyBackedStr = item.get_item(1_i32)?.extract()?;
            if let (Ok(name), Ok(value)) = (
                HeaderName::from_bytes(name.as_bytes()),
                HeaderValue::from_str(&value),
            ) {
                headers.append(name, value);
            }
        }
        *captured.lock().unwrap_or_else(PoisonError::into_inner) = Some((status, headers));
        Ok(())
    })
}

/// Runs entirely in `PyResult`, so every conversion stays inside pyo3's own (`Send`-safe)
/// error type; only the caller converts it to an `eyre::Report`.
fn call(
    py: Python<'_>,
    application: &Py<PyAny>,
    parts: &Parts,
    body: &[u8],
    peer: &Peer,
) -> PyResult<(u16, HeaderMap, Bytes)> {
    let environ = build_environ(py, parts, body, peer)?;
    let captured: StartResponse = Arc::new(Mutex::new(None));
    let start_response = start_response_function(py, Arc::clone(&captured))?;

    let result = application.call1(py, (environ, start_response))?;
    let result = result.bind(py);

    let mut collected = Vec::new();
    for chunk in result.try_iter()? {
        let chunk: PyBackedBytes = chunk?.extract()?;
        collected.extend_from_slice(&chunk);
    }
    if result.hasattr("close")? {
        result.call_method0("close")?;
    }

    let (status, headers) = captured
        .lock()
        .unwrap_or_else(PoisonError::into_inner)
        .take()
        .ok_or_else(|| {
            PyRuntimeError::new_err("the application returned without calling start_response")
        })?;
    Ok((status, headers, Bytes::from(collected)))
}

impl Wsgi {
    pub(super) fn new(application: Py<PyAny>, threads: NonZeroUsize) -> Result<Self> {
        Ok(Self {
            application: Arc::new(application),
            threads: Threads::new(threads)?,
        })
    }

    pub(super) async fn http(&self, request: Request, peer: &Peer) -> Result<Response> {
        let (parts, body) = request.into_parts();
        // ponytail: buffers the request body, which the body limit layer caps. Stream it
        // through `wsgi.input` if large uploads become a problem.
        let body = body.collect().await?.to_bytes();
        let application = Arc::clone(&self.application);
        let peer = peer.clone();

        let (status, headers, body) = self
            .threads
            .run(move |py| call(py, &application, &parts, &body, &peer))
            .await??;

        let mut response = Response::new(Body::from(body));
        *response.status_mut() = StatusCode::from_u16(status)?;
        *response.headers_mut() = headers;
        Ok(response)
    }
}

#[cfg(test)]
mod tests {
    use std::{
        collections::HashSet,
        ffi::CString,
        net::{IpAddr, Ipv4Addr},
    };

    use super::*;

    const APP: &str = r#"
import threading

def app(environ, start_response):
    start_response("200 OK", [("X-Thread", str(threading.get_ident()))])
    return [environ["PATH_INFO"].encode()]
"#;

    fn wsgi() -> Wsgi {
        crate::python::initialize().expect("failed to initialize Python");
        let application = Python::attach(|py| {
            let cwd = std::env::current_dir().expect("no working directory");
            py.import("sys")
                .and_then(|sys| sys.getattr("path"))
                .and_then(|path| path.call_method1("insert", (0_i32, cwd.as_os_str())))
                .expect("failed to set sys.path");
            let code = CString::new(APP).expect("invalid code");
            PyModule::from_code(py, &code, c"test_wsgi_app.py", c"test_wsgi_app")
                .and_then(|module| module.getattr("app"))
                .expect("failed to load the test application")
                .unbind()
        });
        Wsgi::new(application, NonZeroUsize::new(4).expect("non-zero"))
            .expect("failed to start the Python threads")
    }

    fn peer() -> Peer {
        Peer {
            client: IpAddr::V4(Ipv4Addr::new(192, 0, 2, 1)),
            scheme: "http".to_owned(),
        }
    }

    fn request(path: &str) -> Request {
        Request::builder()
            .uri(path)
            .header(HOST, "authentik.company")
            .body(Body::empty())
            .expect("failed to build request")
    }

    #[tokio::test]
    async fn http_request_round_trips() {
        let response = wsgi()
            .http(request("/api/v3/caf%C3%A9/"), &peer())
            .await
            .expect("request failed");

        assert_eq!(response.status(), StatusCode::OK);
        let body = response
            .into_body()
            .collect()
            .await
            .expect("failed to read body")
            .to_bytes();
        assert_eq!(body, "/api/v3/café/");
    }

    /// The whole point of moving HTTP off the single ASGI event-loop thread: requests must
    /// actually land on more than one OS thread, or a free-threaded interpreter buys nothing.
    #[tokio::test]
    async fn concurrent_requests_run_on_distinct_threads() {
        let wsgi = wsgi();
        let peer = peer();
        let responses = futures::future::join_all(
            std::iter::repeat_with(|| wsgi.http(request("/"), &peer)).take(8),
        )
        .await;

        let threads: HashSet<_> = responses
            .into_iter()
            .map(|response| {
                response.expect("request failed").headers()["x-thread"]
                    .to_str()
                    .expect("thread id header")
                    .to_owned()
            })
            .collect();

        assert!(
            threads.len() > 1,
            "all 8 concurrent requests ran on the same thread: {threads:?}"
        );
    }
}
