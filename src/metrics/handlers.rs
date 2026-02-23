use axum::{body::Body, http::StatusCode, response::Response};
use prometheus_client::encoding::text::encode;
use tokio::task::spawn_blocking;

use crate::axum::error::Result;

pub(super) async fn metrics_handler() -> Result<Response> {
    let mut metrics = String::new();

    let registry = super::REGISTRY
        .get()
        .expect("failed to get registry, has it been initialized?")
        .read()
        .await;
    encode(&mut metrics, &registry)?;

    if metrics == "# EOF\n" {
        metrics = String::new();
    }

    #[cfg(feature = "server")]
    {
        metrics.push_str(&String::from_utf8(
            spawn_blocking(python::get_python_metrics).await??,
        )?);
    }

    Ok(Response::builder()
        .status(StatusCode::OK)
        .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
        .body(Body::from(metrics))?)
}

#[cfg(feature = "server")]
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
