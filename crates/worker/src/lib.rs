use std::{
    env,
    io::Write,
    net::SocketAddr,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};

use argh::FromArgs;
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
};
use axum_server::Handle;
use eyre::{Report, Result, eyre};
use nix::{
    sys::{
        signal::{SigSet, SigmaskHow, Signal, kill, pthread_sigmask},
        wait::waitpid,
    },
    unistd::Pid,
};
use pyo3::{
    IntoPyObjectExt,
    ffi::c_str,
    prelude::*,
    types::{IntoPyDict, PyIterator, PyList, PyString},
};
use signal_hook::consts::signal::*;
use tokio::{sync::RwLock, task::JoinSet};
use tracing::{debug, error, info, warn};

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik worker.
#[argh(subcommand, name = "worker")]
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

fn start_local_worker(
    tasks: &mut JoinSet<Result<()>>,
    shutdown: Arc<AtomicBool>,
    threads: usize,
) -> Result<()> {
    let (broker, worker) = Python::attach(|py| {
        let dramatiq_broker = PyModule::import(py, "dramatiq.broker")?;
        let dramatiq_worker = PyModule::import(py, "dramatiq.worker")?;

        debug!("Loading broker...");
        let broker = dramatiq_broker.call_method0("get_broker")?;
        broker.call_method1("emit_after", ("process_boot",))?;

        debug!("Starting worker threads...");
        let worker = dramatiq_worker.call_method(
            "Worker",
            (&broker,),
            Some(&[("worker_threads", threads)].into_py_dict(py)?),
        )?;
        worker.call_method0("start")?;

        debug!("Local worker process is ready for action");

        Ok::<_, Report>((broker.into_py_any(py)?, worker.into_py_any(py)?))
    })?;
    tasks.spawn_blocking(move || {
        while !shutdown.load(Ordering::Relaxed) {
            std::thread::sleep(Duration::from_secs(1));
        }

        Python::attach(|py| {
            let broker = broker.bind(py);
            let worker = worker.bind(py);

            worker.call_method("stop", (), Some(&[("timeout", 600_000)].into_py_dict(py)?))?;
            broker.call_method0("close")?;

            Ok::<_, Report>(())
        })?;
        Ok(())
    });
    Ok(())
}

#[allow(clippy::type_complexity)]
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

#[allow(clippy::type_complexity)]
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

        Ok::<_, Report>((procs, stdout_pipes, stderr_pipes))
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
            if shutdown.load(Ordering::Relaxed) {
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

fn kill_workers(mut state: tokio::sync::RwLockWriteGuard<'_, State>) {
    for worker_process in &mut state.worker_processes {
        if worker_process.killed {
            continue;
        }
        worker_process.killed = true;
        if let Err(err) = kill(worker_process.pid, Signal::SIGTERM) {
            warn!(
                "Failed to send SIGTERM to PID {pid}: {err}",
                pid = worker_process.pid
            );
        } else if let Err(err) = waitpid(worker_process.pid, None) {
            warn!(
                "Failed to wait for PID {pid}: {err}",
                pid = worker_process.pid,
            );
        }
    }
}

fn watch_workers(state_lock: Arc<RwLock<State>>) -> Result<()> {
    loop {
        let state = state_lock.blocking_read();
        if state.shutdown.load(Ordering::Relaxed) {
            drop(state);
            let state = state_lock.blocking_write();
            kill_workers(state);
            return Ok(());
        }

        for worker_process in &state.worker_processes {
            match Python::attach(|py| {
                let proc = worker_process.proc.bind(py);
                proc.call_method("join", (), Some(&[("timeout", 1)].into_py_dict(py)?))?;
                let exitcode = proc.getattr("exitcode")?;
                if exitcode.is_none() {
                    Ok::<_, Report>(None)
                } else {
                    let exitcode: i32 = exitcode.extract()?;
                    Ok(Some(exitcode))
                }
            }) {
                Ok(None) => continue,
                Ok(Some(exitcode)) => {
                    error!(
                        "Worker with PID {} exited unexpectedly (code {exitcode}). Shutting \
                         down...",
                        worker_process.pid
                    );
                    state.shutdown();
                    continue;
                }
                Err(err) => {
                    error!(
                        "Failed to check if worker with PID {} is alive: {err}. Shutting down...",
                        worker_process.pid
                    );
                    state.shutdown();
                    continue;
                }
            }
        }
    }
}

struct State {
    worker_processes: Vec<WorkerProcess>,
    shutdown: Arc<AtomicBool>,
    healthcheck_handle: Handle<SocketAddr>,
    metrics_handle: Handle<SocketAddr>,
}

impl State {
    fn shutdown(&self) {
        self.shutdown.store(true, Ordering::Relaxed);
        self.healthcheck_handle.shutdown();
        self.metrics_handle.shutdown();
    }
}

#[tokio::main]
pub async fn run(_cli: Cli) -> Result<()> {
    // TODO: pyo3-logger
    let processes = 1;
    let threads = 1;

    unsafe { env::set_var("PROMETHEUS_MULTIPROC_DIR", "/tmp/authentik_prometheus_tmp") };
    Python::initialize();
    migrate()?;

    let mut tasks = JoinSet::new();
    let shutdown = Arc::new(AtomicBool::new(false));

    // Start the local worker first. If any issue arise, we'll be able to exit quickly and not deal
    // with forking processes.
    start_local_worker(&mut tasks, Arc::clone(&shutdown), threads)?;

    // To prevent the main process from exiting due to signals after worker
    // processes and fork processes have been defined but before the signal
    // handling has been configured for those processes, block those signals
    // that the main process is expected to handle.
    block_signals()?;

    let worker_processes = if processes > 1 {
        let (worker_processes, stdout_pipes, stderr_pipes) =
            start_worker_processes(processes, threads)?;

        let shutdown_clone = Arc::clone(&shutdown);
        tasks.spawn_blocking(move || watch_logs(std::io::stdout(), stdout_pipes, shutdown_clone));
        let shutdown_clone = Arc::clone(&shutdown);
        tasks.spawn_blocking(move || watch_logs(std::io::stderr(), stderr_pipes, shutdown_clone));

        worker_processes
    } else {
        Vec::new()
    };

    info!("authentik worker is booting up.");

    signal_hook::flag::register(SIGINT, Arc::clone(&shutdown))?;
    signal_hook::flag::register(SIGTERM, Arc::clone(&shutdown))?;
    signal_hook::flag::register(SIGHUP, Arc::clone(&shutdown))?;

    // Now that the watcher threads have been started and the
    // sighandler for the main process has been defined, it should be
    // safe to unblock the signals that were previously blocked.
    unblock_signals()?;

    let state_lock = Arc::new(RwLock::new(State {
        worker_processes,
        shutdown,
        healthcheck_handle: Handle::new(),
        metrics_handle: Handle::new(),
    }));

    if processes > 1 {
        tasks.spawn_blocking({
            let state_lock = Arc::clone(&state_lock);
            move || watch_workers(state_lock)
        });
    }
    tasks.spawn(healthcheck::run(Arc::clone(&state_lock)));
    tasks.spawn(metrics::run(Arc::clone(&state_lock)));
    tasks.spawn(worker_status::run(Arc::clone(&state_lock)));

    if let Some(result) = tasks.join_next().await {
        state_lock.write().await.shutdown();

        let mut errors = Vec::new();

        match result {
            Ok(Ok(_)) => {}
            Ok(Err(err)) => errors.push(err),
            Err(err) => errors.push(Report::new(err)),
        }

        while let Some(result) = tasks.join_next().await {
            match result {
                Ok(Ok(_)) => {}
                Ok(Err(err)) => errors.push(err),
                Err(err) => errors.push(Report::new(err)),
            }
        }

        if !errors.is_empty() {
            return Err(eyre!("Errors encountered in worker: {:?}", errors));
        }
    }

    Ok(())
}

mod healthcheck {
    use std::{net::SocketAddr, sync::Arc};

    use eyre::Result;
    use tokio::sync::RwLock;

    use super::State;

    pub(super) async fn run(state: Arc<RwLock<State>>) -> Result<()> {
        let app = axum::Router::new().fallback(|| async { "ok" });
        let addr = SocketAddr::from(([0, 0, 0, 0], 9000));
        let handle = state.read().await.healthcheck_handle.clone();
        axum_server::bind(addr)
            .handle(handle)
            .serve(app.into_make_service())
            .await?;
        Ok(())
    }
}

mod metrics {
    use std::{net::SocketAddr, sync::Arc};

    use axum::{body::Body, http::StatusCode, response::Response};
    use eyre::Result;
    use pyo3::{
        IntoPyObjectExt,
        ffi::c_str,
        prelude::*,
        types::{PyBytes, PyDict},
    };
    use tokio::sync::RwLock;

    use super::State;
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

    pub(super) async fn run(state: Arc<RwLock<State>>) -> Result<()> {
        let app = axum::Router::new().fallback(axum::routing::any(metrics_handler));
        let addr = SocketAddr::from(([0, 0, 0, 0], 9001));
        let handle = state.read().await.metrics_handle.clone();
        axum_server::bind(addr)
            .handle(handle)
            .serve(app.into_make_service())
            .await?;
        Ok(())
    }
}

mod worker_status {
    use std::{
        sync::{Arc, atomic::Ordering},
        time::Duration,
    };

    use eyre::Result;
    use tokio::sync::RwLock;

    use super::State;

    pub(super) async fn run(state: Arc<RwLock<State>>) -> Result<()> {
        loop {
            if state.read().await.shutdown.load(Ordering::Relaxed) {
                break;
            }
            tokio::time::sleep(Duration::from_secs(5)).await;
        }
        Ok(())
    }
}

struct AppError(eyre::Error);

impl<E> From<E> for AppError
where E: Into<eyre::Error>
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        warn!("Error occurred: {:?}", self.0);
        (StatusCode::INTERNAL_SERVER_ERROR, "Something went wrong").into_response()
    }
}
