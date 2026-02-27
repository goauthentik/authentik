use std::sync::Arc;

use axum::{body::Body, extract::State, http::StatusCode, response::Response};

#[cfg(feature = "core")]
use crate::mode;
use crate::{axum::error::Result, metrics::AppState};

pub(super) async fn metrics_handler(State(state): State<Arc<AppState>>) -> Result<Response> {
    let mut metrics = Vec::new();
    state.prometheus.render_to_write(&mut metrics)?;

    #[cfg(feature = "core")]
    if mode::get() == mode::Mode::Server {
        use axum::http::{
            Request,
            header::{AUTHORIZATION, HOST},
        };

        state
            .core_client
            .request(
                Request::builder()
                    .method("GET")
                    .uri("http://localhost:8000/-/metrics/")
                    .header(HOST, "localhost")
                    .header(AUTHORIZATION, format!("Bearer {}", state.metrics_key))
                    .body(Body::from(""))?,
            )
            .await?;
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
        IntoPyObjectExt,
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
                .unwrap_or(&PyBytes::new(py, &[]))
                .as_bytes()
                .to_owned();
            Ok::<_, Report>(metrics)
        })?;
        Ok::<_, Report>(metrics)
    }
}
