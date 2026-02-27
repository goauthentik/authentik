use std::{
    env,
    path::PathBuf,
    process::Stdio,
    sync::atomic::{AtomicBool, Ordering},
    time::Duration,
};

use argh::FromArgs;
use axum::body::Body;
use eyre::{Result, eyre};
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
use tokio::{
    net::UnixStream,
    process::{Child, Command},
    signal::unix::SignalKind,
    sync::broadcast::error::RecvError,
};
use tracing::{info, trace, warn};

use crate::{
    arbiter::{Arbiter, Tasks},
    config,
};

#[derive(Debug, Default, FromArgs, PartialEq)]
/// Run the authentik worker.
#[argh(subcommand, name = "worker")]
pub(crate) struct Cli {}

const INITIAL_WORKER_ID: usize = 1000;
static INITIAL_WORKER_READY: AtomicBool = AtomicBool::new(false);

type WorkerClient = Client<UnixSocketConnector<PathBuf>, Body>;

fn socket_path() -> PathBuf {
    env::temp_dir().join("authentik-worker.sock")
}

pub(crate) fn build_client() -> WorkerClient {
    let connector = UnixSocketConnector::new(socket_path());
    Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .set_host(false)
        .build(connector)
}

struct Worker(Child);

impl Worker {
    fn new(worker_id: usize) -> Result<Self> {
        info!(worker_id, "Starting worker");
        Ok(Self(
            Command::new("python")
                .args(["-m", "lifecycle.worker_process", &worker_id.to_string()])
                .kill_on_drop(true)
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
        ))
    }

    async fn shutdown(&mut self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to worker"
        );
        if let Some(id) = self.0.id() {
            kill(Pid::from_raw(id as i32), signal)?;
        }
        self.0.wait().await?;
        Ok(())
    }

    async fn graceful_shutdown(&mut self) -> Result<()> {
        info!("gracefully shutting down worker");
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&mut self) -> Result<()> {
        info!("immediately shutting down worker");
        self.shutdown(Signal::SIGINT).await
    }

    async fn is_alive(&mut self) -> bool {
        let try_wait = self.0.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!("worker has exited with status {code}");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!("failed to check the status of worker process, ignoring: {err}");
                true
            }
        }
    }
}

struct Workers(Vec<Worker>);

impl Workers {
    fn new() -> Result<Self> {
        let mut workers = Vec::with_capacity(config::get().worker.processes.get());
        workers.push(Worker::new(INITIAL_WORKER_ID)?);
        Ok(Self(workers))
    }

    fn start_other_workers(&mut self) -> Result<()> {
        for i in 1..config::get().worker.processes.get() {
            self.0.push(Worker::new(INITIAL_WORKER_ID + i)?);
        }
        Ok(())
    }

    async fn graceful_shutdown(&mut self) -> Result<()> {
        let mut results = Vec::with_capacity(self.0.capacity());
        for worker in &mut self.0 {
            results.push(worker.graceful_shutdown().await);
        }

        results.into_iter().find(|r| r.is_err()).unwrap_or(Ok(()))
    }

    async fn fast_shutdown(&mut self) -> Result<()> {
        let mut results = Vec::with_capacity(self.0.capacity());
        for worker in &mut self.0 {
            results.push(worker.fast_shutdown().await);
        }

        results.into_iter().find(|r| r.is_err()).unwrap_or(Ok(()))
    }

    async fn are_alive(&mut self) -> bool {
        for worker in &mut self.0 {
            if !worker.is_alive().await {
                return false;
            }
        }
        true
    }

    async fn is_socket_ready() -> bool {
        let result = UnixStream::connect(socket_path()).await;
        trace!("checking if worker socket is ready: {result:?}");
        result.is_ok()
    }
}

async fn watch_workers(arbiter: Arbiter, mut workers: Workers) -> Result<()> {
    info!("starting worker watcher");
    let mut signals_rx = arbiter.signals_subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        if signal == SignalKind::user_defined2() {
                            info!("worker notified us ready, marked ready for operation");
                            INITIAL_WORKER_READY.store(true, Ordering::Relaxed);
                            workers.start_other_workers()?;
                        }
                    },
                    Err(RecvError::Lagged(_)) => continue,
                    Err(RecvError::Closed) => {
                        warn!("error receiving signals");
                        return Err(RecvError::Closed.into());
                    }
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(1)), if !INITIAL_WORKER_READY.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the worker unix socket and mark ready once it accepts connections.
                if Workers::is_socket_ready().await {
                    info!("worker socket is accepting connections, marked ready for operation");
                    INITIAL_WORKER_READY.store(true, Ordering::Relaxed);
                    workers.start_other_workers()?;
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(5)) => {
                if !workers.are_alive().await {
                    return Err(eyre!("gunicorn has exited unexpectedly"));
                }
            },
            _ = arbiter.fast_shutdown() => {
                workers.fast_shutdown().await?;
                return Ok(());
            },
            _ = arbiter.graceful_shutdown() => {
                workers.graceful_shutdown().await?;
                return Ok(());
            },
        }
    }
}

pub(super) async fn run(_cli: Cli, tasks: &mut Tasks) -> Result<()> {
    let arbiter = tasks.arbiter();

    let workers = Workers::new()?;

    tasks
        .build_task()
        .name(&format!("{}::watch_workers", module_path!()))
        .spawn(watch_workers(arbiter, workers))?;
    Ok(())
}
