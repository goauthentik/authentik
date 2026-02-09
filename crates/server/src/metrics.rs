use axum::routing::any;
use axum_server::Handle;
use eyre::Result;
use std::net::SocketAddr;

use authentik_lib::error::Error;
use axum::{Router, body::Body, http::StatusCode, response::Response};
use pyo3::{
    IntoPyObjectExt,
    ffi::c_str,
    prelude::*,
    types::{PyBytes, PyDict},
};

async fn metrics_handler() -> Result<Response, Error> {
    let metrics = tokio::task::spawn_blocking(|| {
        let metrics = Python::attach(|py| {
            let locals = PyDict::new(py);
            Python::run(
                py,
                c_str!(
                    r#"
import os
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    generate_latest,
    multiprocess,
)

print(os.environ.get("PROMETHEUS_MULTIPROC_DIR"))
registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)
output = generate_latest(registry)
"#
                ),
                None,
                Some(&locals),
            )?;
            let metrics = locals
                .get_item("output")?
                .unwrap_or(PyBytes::new(py, &[]).into_bound_py_any(py)?)
                .cast::<PyBytes>()
                .unwrap()
                .as_bytes()
                .to_owned();
            Ok::<_, eyre::Error>(metrics)
        })?;
        Ok::<_, eyre::Error>(metrics)
    })
    .await??;
    Ok(Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
        .body(Body::from(metrics))
        .unwrap())
}

pub(super) fn build_router() -> Router {
    Router::new().fallback(any(metrics_handler))
}

pub(super) async fn start_server(
    router: Router,
    addr: SocketAddr,
    handle: Handle<SocketAddr>,
) -> Result<()> {
    axum_server::Server::bind(addr)
        .handle(handle)
        .serve(router.into_make_service_with_connect_info::<SocketAddr>())
        .await?;

    Ok(())
}
