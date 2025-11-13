use nix::libc::pid_t;
use nix::sys::signal::SigSet;
use nix::sys::signal::SigmaskHow;
use nix::sys::signal::Signal;
use nix::sys::signal::kill;
use nix::sys::signal::pthread_sigmask;
use nix::unistd::Pid;
use pyo3::IntoPyObjectExt;
use pyo3::types::IntoPyDict;
use pyo3::types::PyIterator;
use pyo3::types::PyList;
use pyo3::types::PyString;
use signal_hook::consts::signal::*;
use std::env;
use std::io::Write;
use std::process::ExitCode;
use std::sync::Arc;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering;
use tokio::sync::RwLock;
use tracing::{error, info, warn};

use clap::Parser;
use color_eyre::eyre::Result;
use pyo3::{ffi::c_str, prelude::*};

shadow_rs::shadow!(build);

#[derive(Debug, Parser)]
#[command(version = build::CLAP_LONG_VERSION, about, long_about = None)]
pub struct Cli {}

struct WorkerProcess {
    pid: Pid,
    proc: Py<PyAny>,
    killed: bool,
}

fn migrate() -> Result<()> {
    Python::attach(|py| {
        let setup = PyModule::import(py, "authentik.root.setup")?;
        setup.getattr("setup")?.call0()?;
        let lifecycle = PyModule::import(py, "lifecycle.migrate")?;
        lifecycle.getattr("run_migrations")?.call0()?;
        let django_db = PyModule::import(py, "django.db")?;
        django_db
            .getattr("connections")?
            .getattr("close_all")?
            .call0()?;
        Ok(())
    })
}

fn handled_signals() -> SigSet {
    let mut sigset = SigSet::empty();
    sigset.add(Signal::SIGINT);
    sigset.add(Signal::SIGTERM);
    sigset.add(Signal::SIGHUP);
    sigset
}

fn block_signals() -> Result<()> {
    pthread_sigmask(SigmaskHow::SIG_BLOCK, Some(&handled_signals()), None)?;
    Ok(())
}

fn unblock_signals() -> Result<()> {
    pthread_sigmask(SigmaskHow::SIG_UNBLOCK, Some(&handled_signals()), None)?;
    Ok(())
}

fn make_pipes<'a>(
    py: Python<'a>,
) -> Result<(Py<PyAny>, Bound<'a, PyAny>, Py<PyAny>, Bound<'a, PyAny>)> {
    let dramatiq_compat = PyModule::import(py, "dramatiq.compat")?;
    let multiprocessing = PyModule::import(py, "multiprocessing")?;

    let pipe_kwargs = [("duplex", false)].into_py_dict(py)?;

    let (stdout_read_pipe, stdout_write_pipe): (Py<PyAny>, Bound<'a, PyAny>) = multiprocessing
        .call_method("Pipe", (), Some(&pipe_kwargs))?
        .extract()?;
    let (stderr_read_pipe, stderr_write_pipe): (Py<PyAny>, Bound<'a, PyAny>) = multiprocessing
        .call_method("Pipe", (), Some(&pipe_kwargs))?
        .extract()?;

    Ok((
        stdout_read_pipe,
        dramatiq_compat.call_method1("StreamablePipe", (stdout_write_pipe,))?,
        stderr_read_pipe,
        dramatiq_compat.call_method1("StreamablePipe", (stderr_write_pipe,))?,
    ))
}

fn start_worker_processes(
    processes: usize,
    threads: usize,
) -> Result<(Vec<WorkerProcess>, Vec<Py<PyAny>>, Vec<Py<PyAny>>)> {
    let (procs, stdout_pipes, stderr_pipes) = Python::attach(|py| {
        let multiprocessing = PyModule::import(py, "multiprocessing")?;
        let worker_process = PyModule::from_code(
            py,
            c_str!(include_str!(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/src/worker_process.py"
            ))),
            c_str!("worker_process.py"),
            c_str!("worker_process"),
        )?;

        let mut procs = Vec::with_capacity(processes - 1);
        let mut stdout_pipes = Vec::with_capacity(processes);
        let mut stderr_pipes = Vec::with_capacity(processes);

        for worker_id in 1..processes {
            let (stdout_read_pipe, stdout_write_pipe, stderr_read_pipe, stderr_write_pipe) =
                make_pipes(py)?;

            let proc = multiprocessing.call_method(
                "Process",
                (),
                Some(
                    &[
                        ("target", worker_process.getattr("worker_process")?),
                        (
                            "args",
                            (worker_id, threads, &stdout_write_pipe, &stderr_write_pipe)
                                .into_bound_py_any(py)?,
                        ),
                        ("daemon", false.into_bound_py_any(py)?),
                    ]
                    .into_py_dict(py)?,
                ),
            )?;
            proc.call_method0("start")?;

            procs.push(WorkerProcess {
                pid: Pid::from_raw(proc.getattr("pid")?.extract()?),
                proc: proc.into_py_any(py)?,
                killed: false,
            });

            stdout_pipes.push(stdout_read_pipe);
            stderr_pipes.push(stderr_read_pipe);
            stdout_write_pipe.call_method0("close")?;
            stderr_write_pipe.call_method0("close")?;
        }

        Ok::<_, color_eyre::eyre::Error>((procs, stdout_pipes, stderr_pipes))
    })?;
    Ok((procs, stdout_pipes, stderr_pipes))
}

fn watch_logs(mut out: impl Write, pipes: Vec<Py<PyAny>>, shutdown: Arc<AtomicBool>) -> Result<()> {
    Python::attach(|py| {
        let pipes = PyList::new(py, pipes)?;

        let worker_process = PyModule::from_code(
            py,
            c_str!(include_str!(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/src/log_watcher.py"
            ))),
            c_str!("log_watcher.py"),
            c_str!("log_watcher"),
        )?;

        loop {
            if pipes.is_empty() {
                break;
            }
            if shutdown.load(Ordering::Acquire) {
                break;
            }

            let logs = worker_process.call_method1("watch_logs", (&pipes,))?;
            for log in PyIterator::from_object(&logs)? {
                let log: Bound<'_, PyString> = match log?.cast_into() {
                    Ok(log) => log,
                    Err(_) => continue,
                };
                let data = log.to_str()?;
                out.write_all(data.as_bytes())?;
                out.flush()?;
            }
        }
        Ok(())
    })
}

struct State {
    worker_processes: Vec<WorkerProcess>,
    stdout_watcher: std::thread::JoinHandle<Result<()>>,
    stderr_watcher: std::thread::JoinHandle<Result<()>>,
    shutdown: Arc<AtomicBool>,
}

pub fn run(_cli: Cli) -> Result<()> {
    // TODO: pyo3-logger
    let processes = 1;
    let threads = 1;

    Python::initialize();
    migrate()?;

    // To prevent the main process from exiting due to signals after worker
    // processes and fork processes have been defined but before the signal
    // handling has been configured for those processes, block those signals
    // that the main process is expected to handle.
    block_signals()?;

    let (worker_processes, stdout_pipes, stderr_pipes) =
        start_worker_processes(processes, threads)?;

    let shutdown = Arc::new(AtomicBool::new(false));

    let shutdown_clone = Arc::clone(&shutdown);
    let stdout_watcher =
        std::thread::spawn(move || watch_logs(std::io::stdout(), stdout_pipes, shutdown_clone));
    let shutdown_clone = Arc::clone(&shutdown);
    let stderr_watcher =
        std::thread::spawn(move || watch_logs(std::io::stderr(), stderr_pipes, shutdown_clone));

    info!("authentik worker is booting up.");

    signal_hook::flag::register(SIGINT, Arc::clone(&shutdown))?;
    signal_hook::flag::register(SIGTERM, Arc::clone(&shutdown))?;
    signal_hook::flag::register(SIGHUP, Arc::clone(&shutdown))?;

    // Now that the watcher threads have been started and the
    // sighandler for the main process has been defined, it should be
    // safe to unblock the signals that were previously blocked.
    unblock_signals()?;

    let state = State {
        worker_processes,
        stdout_watcher,
        stderr_watcher,
        shutdown,
    };

    main_loop(state)
}

fn kill_workers(mut state: tokio::sync::RwLockWriteGuard<'_, State>) {
    for worker_process in &mut state.worker_processes {
        worker_process.killed = true;
        if let Err(err) = kill(worker_process.pid, Signal::SIGTERM) {
            warn!(
                "Failed to send SIGTERM to PID {pid}: {err}",
                pid = worker_process.pid
            );
        }
    }
}

fn watch_workers(state_lock: Arc<RwLock<State>>) -> Result<ExitCode> {
    loop {
        let state = state_lock.blocking_read();
        if state.shutdown.load(Ordering::Relaxed) {
            drop(state);
            let state = state_lock.blocking_write();
            kill_workers(state);
            return Ok(ExitCode::SUCCESS);
        }

        for worker_process in &state.worker_processes {
            match Python::attach(|py| {
                let proc = worker_process.proc.bind(py);
                proc.call_method("join", (), Some(&[("timeout", 1)].into_py_dict(py)?))?;
                let exit_code = proc.getattr("exitcode")?;
                if exit_code.is_none() {
                    Ok::<_, color_eyre::eyre::Error>(None)
                } else {
                    let exit_code = exit_code.extract()?;
                    error!(
                        "Worker with PID {} exited unexpectedly (code {}). Shutting down...",
                        worker_process.pid, exit_code
                    );
                    Ok(Some(exit_code))
                }
            }) {
                Ok(None) => continue,
                Ok(Some(exit_code)) => {
                    state.shutdown.store(true, Ordering::Acquire);
                }
                Err(err) => {
                    state.shutdown.store(true, Ordering::Acquire);
                }
            }
        }
    }
}

#[tokio::main]
async fn main_loop(state: State) -> Result<()> {
    let state = Arc::new(RwLock::new(state));
    let workers_watcher = tokio::spawn(watch_workers(Arc::clone(&state)));
    Ok(())
}

// #[tokio::main]
// pub async fn run(_cli: Cli) -> Result<()> {
//     unsafe {
//         env::set_var("PROMETHEUS_MULTIPROC_DIR", "/tmp/authentik_prometheus_tmp");
//     }
//
//     let dramatiq_task = tokio::task::spawn_blocking(move || {
//         Python::initialize();
//         setup()?;
//         let exit_code = run_dramatiq()?;
//         Ok::<_, color_eyre::eyre::Error>(exit_code)
//     });
//
//     let healthcheck_handle = Handle::new();
//     let healthcheck = tokio::spawn(healthcheck::run(healthcheck_handle.clone()));
//     let metrics_handle = Handle::new();
//     let metrics = tokio::spawn(metrics::run(metrics_handle.clone()));
//     let worker_status_handle = Handle::new();
//     let worker_status = tokio::spawn(worker_status::run(worker_status_handle.clone()));
//
//     let shutdown = || async {
//         healthcheck_handle.shutdown();
//         metrics_handle.shutdown();
//         worker_status_handle.shutdown();
//         healthcheck.await??;
//         metrics.await??;
//         worker_status.await??;
//         Ok::<_, color_eyre::eyre::Error>(())
//     };
//
//     match dramatiq_task.await? {
//         Ok(exit_code) => {
//             shutdown().await?;
//             exit(exit_code);
//         }
//         Err(err) => {
//             shutdown().await?;
//             return Err(err);
//         }
//     }
// }

// fn run_dramatiq() -> Result<i32> {
//     let exit_code = Python::attach(|py| {
//         let dramatiq_args = PyModule::from_code(
//             py,
//             c_str!(include_str!(concat!(
//                 env!("CARGO_MANIFEST_DIR"),
//                 "/src/dramatiq_args.py"
//             ))),
//             c_str!("dramatiq_args.py"),
//             c_str!("dramatiq_args"),
//         )?;
//         let args = dramatiq_args.getattr("args")?;
//
//         let django_db = PyModule::import(py, "django.db")?;
//         django_db
//             .getattr("connections")?
//             .getattr("close_all")?
//             .call0()?;
//
//         let dramatiq_cli = PyModule::import(py, "dramatiq.cli")?;
//
//         let exit_code: i32 = dramatiq_cli.call_method1("main", (args,))?.extract()?;
//
//         Ok::<_, color_eyre::eyre::Error>(exit_code)
//     })?;
//     Ok(exit_code)
// }
//
// mod healthcheck {
//     use std::net::SocketAddr;
//
//     use axum_server::Handle;
//     use color_eyre::eyre::Result;
//
//     pub(super) async fn run(handle: Handle) -> Result<()> {
//         let app = axum::Router::new().fallback(|| async { "ok" });
//         let addr = SocketAddr::from(([0, 0, 0, 0], 9000));
//         axum_server::bind(addr)
//             .handle(handle)
//             .serve(app.into_make_service())
//             .await?;
//         Ok(())
//     }
// }
//
// mod metrics {
//     use std::net::SocketAddr;
//
//     use axum::body::Body;
//     use axum::http::StatusCode;
//     use axum::response::{IntoResponse, Response};
//     use axum_server::Handle;
//     use color_eyre::eyre::Result;
//     use pyo3::ffi::c_str;
//     use pyo3::types::{PyBytes, PyDict, PyString};
//     use pyo3::{IntoPyObjectExt, prelude::*};
//
//     use crate::AppError;
//
//     async fn metrics_handler() -> Result<Response, AppError> {
//         let metrics = tokio::task::spawn_blocking(|| {
//             let metrics = Python::attach(|py| {
//                 let locals = PyDict::new(py);
//                 Python::run(
//                     py,
//                     c_str!(
//                         r#"
// from prometheus_client import (
//     CONTENT_TYPE_LATEST,
//     CollectorRegistry,
//     generate_latest,
//     multiprocess,
// )
//
// registry = CollectorRegistry()
// multiprocess.MultiProcessCollector(registry)
// output = generate_latest(registry)
// "#
//                     ),
//                     None,
//                     Some(&locals),
//                 )?;
//                 let metrics = locals
//                     .get_item("output")?
//                     .unwrap_or(PyBytes::new(py, &[]).into_bound_py_any(py)?)
//                     .cast::<PyBytes>()
//                     .unwrap()
//                     .as_bytes()
//                     .to_owned();
//                 Ok::<_, color_eyre::eyre::Error>(metrics)
//             })?;
//             Ok::<_, color_eyre::eyre::Error>(metrics)
//         })
//         .await??;
//         Ok(Response::builder()
//             .status(StatusCode::OK)
//             .header("Content-Type", "text/plain; version=1.0.0; charset=utf-8")
//             .body(Body::from(metrics))
//             .unwrap())
//     }
//
//     pub(super) async fn run(handle: Handle) -> Result<()> {
//         let app = axum::Router::new().fallback(axum::routing::any(metrics_handler));
//         let addr = SocketAddr::from(([0, 0, 0, 0], 9001));
//         axum_server::bind(addr)
//             .handle(handle)
//             .serve(app.into_make_service())
//             .await?;
//         Ok(())
//     }
// }
//
// mod worker_status {
//     use std::net::SocketAddr;
//
//     use axum_server::Handle;
//     use color_eyre::eyre::Result;
//
//     pub(super) async fn run(handle: Handle) -> Result<()> {
//         let app = axum::Router::new().fallback(|| async { "ok" });
//         let addr = SocketAddr::from(([0, 0, 0, 0], 9002));
//         axum_server::bind(addr)
//             .handle(handle)
//             .serve(app.into_make_service())
//             .await?;
//         Ok(())
//     }
// }
//
// struct AppError(color_eyre::eyre::Error);
//
// impl<E> From<E> for AppError
// where
//     E: Into<color_eyre::eyre::Error>,
// {
//     fn from(err: E) -> Self {
//         Self(err.into())
//     }
// }
//
// impl IntoResponse for AppError {
//     fn into_response(self) -> Response {
//         (
//             StatusCode::INTERNAL_SERVER_ERROR,
//             format!("Something went wrong"),
//         )
//             .into_response()
//     }
// }
