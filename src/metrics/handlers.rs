use axum::{body::Body, http::StatusCode, response::Response};
use eyre::Report;
use pyo3::{
    IntoPyObjectExt,
    ffi::c_str,
    prelude::*,
    types::{PyBytes, PyDict},
};

use crate::axum::error::Result;

pub(super) async fn metrics_handler() -> Result<Response> {
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
            Ok::<_, Report>(metrics)
        })?;
        Ok::<_, Report>(metrics)
    })
    .await??;
    Ok(Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
        .body(Body::from(metrics))
        .unwrap())
}
