use std::{
    env::temp_dir,
    os::unix,
    path::PathBuf,
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
};

use ak_common::{
    Event,
    arbiter::{Arbiter, Tasks},
    config,
    mode::Mode,
};
use argh::FromArgs;
use axum::{
    body::Body,
    http::{Request, header::HOST},
};
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
    sync::Mutex,
    time::{Duration, interval},
};
use tracing::{info, instrument, trace, warn};

use crate::server::socket_path;

mod healthcheck;
mod worker_status;

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik worker.
#[argh(subcommand, name = "worker")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

const INITIAL_WORKER_ID: usize = 1000;
static INITIAL_WORKER_READY: AtomicBool = AtomicBool::new(false);

pub(crate) struct Worker {
    worker_id: usize,
    worker: Child,
    client: Client<UnixSocketConnector<PathBuf>, Body>,
    socket_path: PathBuf,
}

impl Worker {
    fn new(worker_id: usize, socket_path: PathBuf) -> Result<Self> {
        info!(worker_id, "starting worker");

        let mut cmd = Command::new("python");
        cmd.arg("-m");
        cmd.arg("lifecycle.worker_process");
        cmd.arg(worker_id.to_string());
        cmd.arg(&socket_path);

        let client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_mins(1))
            .set_host(false)
            .build(UnixSocketConnector::new(socket_path.clone()));

        Ok(Self {
            worker_id,
            worker: cmd
                .kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
            client,
            socket_path,
        })
    }

    async fn shutdown(&mut self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to worker"
        );
        if let Some(id) = self.worker.id() {
            kill(Pid::from_raw(id.cast_signed()), signal)?;
        }
        self.worker.wait().await?;
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

    #[instrument(skip(self), fields(worker_id = self.worker_id))]
    fn is_alive(&mut self) -> bool {
        let try_wait = self.worker.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!(?code, "worker has exited");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!(
                    ?err,
                    "failed to check the status of worker process, ignoring"
                );
                true
            }
        }
    }

    async fn is_socket_ready(&self) -> bool {
        let result = UnixStream::connect(&self.socket_path).await;
        trace!(?result, "checking if worker socket is ready");
        result.is_ok()
    }

    #[instrument(skip(self), fields(worker_id = self.worker_id))]
    async fn health_live(&self) -> Result<bool> {
        trace!("sending health live request to worker");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/live/")
            .header(HOST, "localhost")
            .body(Body::from(""))?;
        Ok(self
            .client
            .request(req)
            .await
            .inspect_err(|err| warn!(?err, "failed to send health live request to worker"))?
            .status()
            .is_success())
    }

    #[instrument(skip(self), fields(worker_id = self.worker_id))]
    async fn health_ready(&self) -> Result<bool> {
        trace!("sending health ready request to worker");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/ready/")
            .header(HOST, "localhost")
            .body(Body::from(""))?;
        Ok(self
            .client
            .request(req)
            .await
            .inspect_err(|err| warn!(?err, "failed to send health ready request to worker"))?
            .status()
            .is_success())
    }

    #[instrument(skip(self), fields(worker_id = self.worker_id))]
    async fn notify_metrics(&self) -> Result<()> {
        trace!("sending metrics request to worker");
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/metrics/")
            .header(HOST, "localhost")
            .body(Body::from(""))?;
        self.client
            .request(req)
            .await
            .inspect_err(|err| warn!(?err, "failed to send metrics request to worker"))?;
        Ok(())
    }
}

impl Drop for Worker {
    fn drop(&mut self) {
        if let Err(err) = std::fs::remove_file(&self.socket_path) {
            trace!(?err, "failed to remove socket, ignoring");
        }
    }
}

pub(crate) struct Workers(Mutex<Vec<Worker>>);

impl Workers {
    fn new() -> Result<Self> {
        let mut workers = Vec::with_capacity(config::get().worker.processes.get());
        workers.push(Worker::new(
            INITIAL_WORKER_ID,
            temp_dir().join(format!("authentik-worker-{INITIAL_WORKER_ID}.sock")),
        )?);

        Ok(Self(Mutex::new(workers)))
    }

    async fn start_other_workers(&self) -> Result<()> {
        let mut workers = self.0.lock().await;
        while workers.len() != config::get().worker.processes.get() {
            let worker_id = INITIAL_WORKER_ID + workers.len();
            workers.push(Worker::new(
                worker_id,
                temp_dir().join(format!("authentik-worker-{worker_id}.sock")),
            )?);
        }
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        let mut results = Vec::with_capacity(self.0.lock().await.capacity());
        for worker in self.0.lock().await.iter_mut() {
            results.push(worker.graceful_shutdown().await);
        }

        results.into_iter().find(Result::is_err).unwrap_or(Ok(()))
    }

    async fn fast_shutdown(&self) -> Result<()> {
        let mut results = Vec::with_capacity(self.0.lock().await.capacity());
        for worker in self.0.lock().await.iter_mut() {
            results.push(worker.fast_shutdown().await);
        }

        results.into_iter().find(Result::is_err).unwrap_or(Ok(()))
    }

    #[instrument(skip_all)]
    async fn are_alive(&self) -> bool {
        for worker in self.0.lock().await.iter_mut() {
            if !worker.is_alive() {
                return false;
            }
        }
        true
    }

    async fn is_socket_ready(&self) -> bool {
        if let Some(initial_worker) = self.0.lock().await.iter_mut().next() {
            return initial_worker.is_socket_ready().await;
        }
        false
    }

    #[instrument(skip_all)]
    async fn health_live(&self) -> Result<bool> {
        for worker in self.0.lock().await.iter() {
            if !worker.health_live().await? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    #[instrument(skip_all)]
    async fn health_ready(&self) -> Result<bool> {
        for worker in self.0.lock().await.iter() {
            if !worker.health_ready().await? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    #[instrument(skip_all)]
    pub(crate) async fn notify_metrics(&self) -> Result<()> {
        if let Some(worker) = self.0.lock().await.iter().next() {
            worker.notify_metrics().await?;
        }
        Ok(())
    }
}

async fn watch_workers(arbiter: Arbiter, workers: Arc<Workers>) -> Result<()> {
    info!("starting worker watcher");
    let mut events_rx = arbiter.events_subscribe();
    let mut check_interval = interval(Duration::from_secs(5));
    let mut start_interval = interval(Duration::from_secs(1));

    loop {
        tokio::select! {
            Ok(Event::Signal(signal)) = events_rx.recv() => {
                if signal == SignalKind::user_defined2() && !INITIAL_WORKER_READY.load(Ordering::Relaxed) {
                    info!("worker notified us ready, marked ready for operation");
                    INITIAL_WORKER_READY.store(true, Ordering::Relaxed);
                    workers.start_other_workers().await?;
                }
            },
            _ = start_interval.tick(), if !INITIAL_WORKER_READY.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the worker unix socket and mark ready once it accepts connections.
                if workers.is_socket_ready().await {
                    info!("worker socket is accepting connections, marked ready for operation");
                    INITIAL_WORKER_READY.store(true, Ordering::Relaxed);
                    workers.start_other_workers().await?;
                }
            },
            _ = check_interval.tick() => {
                if !workers.are_alive().await {
                    return Err(eyre!("one or more workers have exited unexpectedly"));
                }
            },
            () = arbiter.fast_shutdown() => {
                workers.fast_shutdown().await?;
                return Ok(());
            },
            () = arbiter.graceful_shutdown() => {
                workers.graceful_shutdown().await?;
                return Ok(());
            },
        }
    }
}

pub(crate) fn start(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Workers>> {
    let arbiter = tasks.arbiter();

    let workers = Arc::new(Workers::new()?);

    tasks
        .build_task()
        .name(&format!("{}::watch_workers", module_path!()))
        .spawn(watch_workers(arbiter.clone(), Arc::clone(&workers)))?;

    tasks
        .build_task()
        .name(&format!("{}::worker_status::run", module_path!()))
        .spawn(worker_status::run(arbiter))?;

    // Only run HTTP server in worker mode, in allinone mode, they're handled by the server.
    if Mode::get() == Mode::Worker {
        let router = healthcheck::build_router(Arc::clone(&workers));

        for addr in config::get().listen.http.iter().copied() {
            ak_axum::server::start_plain(tasks, "worker", router.clone(), addr)?;
        }

        ak_axum::server::start_unix(
            tasks,
            "worker",
            router,
            unix::net::SocketAddr::from_pathname(socket_path())?,
        )?;
    }

    Ok(workers)
}
