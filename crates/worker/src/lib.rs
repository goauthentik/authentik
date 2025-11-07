use axum::response::IntoResponse;
use axum::response::Response;
use std::{env, process::exit};

use axum::http::StatusCode;
use axum_server::Handle;
use clap::Parser;
use color_eyre::eyre::Result;
use pyo3::{ffi::c_str, prelude::*};

shadow_rs::shadow!(build);

#[derive(Debug, Parser)]
#[command(version = build::CLAP_LONG_VERSION, about, long_about = None)]
pub struct Cli {}

#[tokio::main]
pub async fn run(_cli: Cli) -> Result<()> {
    unsafe {
        env::set_var("PROMETHEUS_MULTIPROC_DIR", "/tmp/authentik_prometheus_tmp");
    }

    let dramatiq_task = tokio::task::spawn_blocking(move || {
        Python::initialize();
        setup()?;
        let exit_code = run_dramatiq()?;
        Ok::<_, color_eyre::eyre::Error>(exit_code)
    });

    let healthcheck_handle = Handle::new();
    let healthcheck = tokio::spawn(healthcheck::run(healthcheck_handle.clone()));
    let metrics_handle = Handle::new();
    let metrics = tokio::spawn(metrics::run(metrics_handle.clone()));
    let worker_status_handle = Handle::new();
    let worker_status = tokio::spawn(worker_status::run(worker_status_handle.clone()));

    let shutdown = || async {
        healthcheck_handle.shutdown();
        metrics_handle.shutdown();
        worker_status_handle.shutdown();
        healthcheck.await??;
        metrics.await??;
        worker_status.await??;
        Ok::<_, color_eyre::eyre::Error>(())
    };

    match dramatiq_task.await? {
        Ok(exit_code) => {
            shutdown().await?;
            exit(exit_code);
        }
        Err(err) => {
            shutdown().await?;
            return Err(err);
        }
    }
}

fn setup() -> Result<()> {
    Python::attach(|py| {
        let setup = PyModule::import(py, "authentik.root.setup")?;
        setup.getattr("setup")?.call0()?;
        let lifecycle = PyModule::import(py, "lifecycle.migrate")?;
        lifecycle.getattr("run_migrations")?.call0()?;
        Ok(())
    })
}

fn run_dramatiq() -> Result<i32> {
    let exit_code = Python::attach(|py| {
        let dramatiq_args = PyModule::from_code(
            py,
            c_str!(include_str!(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/src/dramatiq_args.py"
            ))),
            c_str!("dramatiq_args.py"),
            c_str!("dramatiq_args"),
        )?;
        let args = dramatiq_args.getattr("args")?;

        let django_db = PyModule::import(py, "django.db")?;
        django_db
            .getattr("connections")?
            .getattr("close_all")?
            .call0()?;

        let dramatiq_cli = PyModule::import(py, "dramatiq.cli")?;

        let exit_code: i32 = dramatiq_cli.call_method1("main", (args,))?.extract()?;

        Ok::<_, color_eyre::eyre::Error>(exit_code)
    })?;
    Ok(exit_code)
}

mod healthcheck {
    use std::net::SocketAddr;

    use axum_server::Handle;
    use color_eyre::eyre::Result;

    pub(super) async fn run(handle: Handle) -> Result<()> {
        let app = axum::Router::new().fallback(|| async { "ok" });
        let addr = SocketAddr::from(([0, 0, 0, 0], 9000));
        axum_server::bind(addr)
            .handle(handle)
            .serve(app.into_make_service())
            .await?;
        Ok(())
    }
}

mod metrics {
    use std::net::SocketAddr;

    use axum::body::Body;
    use axum::http::StatusCode;
    use axum::response::{IntoResponse, Response};
    use axum_server::Handle;
    use color_eyre::eyre::Result;
    use pyo3::ffi::c_str;
    use pyo3::types::{PyBytes, PyDict, PyString};
    use pyo3::{IntoPyObjectExt, prelude::*};

    use crate::AppError;

    async fn metrics_handler() -> Result<Response, AppError> {
        let metrics = tokio::task::spawn_blocking(|| {
            let metrics = Python::attach(|py| {
                let locals = PyDict::new(py);
                Python::run(
                    py,
                    c_str!(
                        r#"
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
                Ok::<_, color_eyre::eyre::Error>(metrics)
            })?;
            Ok::<_, color_eyre::eyre::Error>(metrics)
        })
        .await??;
        Ok(Response::builder()
            .status(StatusCode::OK)
            .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
            .body(Body::from(metrics))
            .unwrap())
    }

    pub(super) async fn run(handle: Handle) -> Result<()> {
        let app = axum::Router::new().fallback(axum::routing::any(metrics_handler));
        let addr = SocketAddr::from(([0, 0, 0, 0], 9001));
        axum_server::bind(addr)
            .handle(handle)
            .serve(app.into_make_service())
            .await?;
        Ok(())
    }
}

mod worker_status {
    use std::net::SocketAddr;

    use axum_server::Handle;
    use color_eyre::eyre::Result;

    pub(super) async fn run(handle: Handle) -> Result<()> {
        let app = axum::Router::new().fallback(|| async { "ok" });
        let addr = SocketAddr::from(([0, 0, 0, 0], 9002));
        axum_server::bind(addr)
            .handle(handle)
            .serve(app.into_make_service())
            .await?;
        Ok(())
    }
}

struct AppError(color_eyre::eyre::Error);

impl<E> From<E> for AppError
where
    E: Into<color_eyre::eyre::Error>,
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            format!("Something went wrong"),
        )
            .into_response()
    }
}
