use std::sync::Arc;

use axum::{body::Body, extract::State, http::StatusCode, response::Response};

#[cfg(feature = "core")]
use crate::mode::Mode;
use crate::{axum::error::Result, metrics::Metrics};

pub(super) async fn metrics_handler(State(state): State<Arc<Metrics>>) -> Result<Response> {
    let mut metrics = Vec::new();
    state.prometheus.render_to_write(&mut metrics)?;

    #[cfg(feature = "core")]
    if Mode::is_core() {
        use axum::http::{Request, header::HOST};
        use http_body_util::BodyExt as _;

        if Mode::get() == Mode::AllInOne || Mode::get() == Mode::Server {
            let req = Request::builder()
                .method("GET")
                .uri("http://localhost/metrics")
                .header(HOST, "localhost")
                .body(Body::from(""))?;
            if let Some(server) = state.server.load_full() {
                let data = server
                    .metrics_client
                    .request(req)
                    .await?
                    .into_body()
                    .collect()
                    .await?
                    .to_bytes();
                metrics.extend(&data);
            }
        } else if Mode::get() == Mode::Worker {
            let req = Request::builder()
                .method("GET")
                .uri("http://localhost:8000/-/metrics/")
                .header(HOST, "localhost")
                .body(Body::from(""))?;
            if let Some(workers) = state.workers.load_full() {
                workers.client.request(req).await?;
            }
        }

        metrics.extend(tokio::task::spawn_blocking(python::get_python_metrics).await??);
    }

    Ok(Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
        .body(Body::from(metrics))?)
}

#[cfg(feature = "core")]
mod python {
    use eyre::{Report, Result};
    use pyo3::{
        IntoPyObjectExt as _,
        ffi::c_str,
        prelude::*,
        types::{PyBytes, PyDict},
    };

    pub(super) fn get_python_metrics() -> Result<Vec<u8>> {
        let metrics = Python::attach(|py| {
            let locals = PyDict::new(py);
            Python::run(
                py,
                c_str!(
                    r#"
from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    multiprocess,
)

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
                .map_or_else(|_| PyBytes::new(py, &[]), |v| v.to_owned())
                .as_bytes()
                .to_owned();
            Ok::<_, Report>(metrics)
        })?;
        Ok::<_, Report>(metrics)
    }
}
