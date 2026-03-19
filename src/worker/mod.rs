use std::{
    env::temp_dir,
    os::unix,
    path::PathBuf,
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
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
    sync::{Mutex, broadcast::error::RecvError},
};
use tracing::{info, trace, warn};

use crate::{
    arbiter::{Arbiter, Tasks},
    axum::server,
    config,
    mode::Mode,
};

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik worker.
#[argh(subcommand, name = "worker")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub struct Cli {}

const INITIAL_WORKER_ID: usize = 1000;
static INITIAL_WORKER_READY: AtomicBool = AtomicBool::new(false);

struct Worker(Child);

impl Worker {
    fn new(worker_id: usize, socket_path: Option<&str>) -> Result<Self> {
        info!(worker_id, "Starting worker");
        let mut cmd = Command::new("python");
        cmd.args(["-m", "lifecycle.worker_process", &worker_id.to_string()]);
        if let Some(socket_path) = socket_path {
            cmd.arg(socket_path);
        }
        Ok(Self(
            cmd.kill_on_drop(true)
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
            kill(Pid::from_raw(id.cast_signed()), signal)?;
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

    fn is_alive(&mut self) -> bool {
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

pub struct Workers {
    workers: Mutex<Vec<Worker>>,
    socket_path: PathBuf,
    pub(crate) client: Client<UnixSocketConnector<PathBuf>, Body>,
}

impl Workers {
    fn new(socket_path: PathBuf) -> Result<Self> {
        let mut workers = Vec::with_capacity(config::get().worker.processes.get());
        workers.push(Worker::new(
            INITIAL_WORKER_ID,
            Some(&format!("{}", &socket_path.display())),
        )?);

        let client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_secs(60))
            .set_host(false)
            .build(UnixSocketConnector::new(socket_path.clone()));

        Ok(Self {
            workers: Mutex::new(workers),
            socket_path,
            client,
        })
    }

    async fn start_other_workers(&self) -> Result<()> {
        for i in 1..config::get().worker.processes.get() {
            self.workers
                .lock()
                .await
                .push(Worker::new(INITIAL_WORKER_ID + i, None)?);
        }
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        let mut results = Vec::with_capacity(self.workers.lock().await.capacity());
        for worker in self.workers.lock().await.iter_mut() {
            results.push(worker.graceful_shutdown().await);
        }

        results.into_iter().find(Result::is_err).unwrap_or(Ok(()))
    }

    async fn fast_shutdown(&self) -> Result<()> {
        let mut results = Vec::with_capacity(self.workers.lock().await.capacity());
        for worker in self.workers.lock().await.iter_mut() {
            results.push(worker.fast_shutdown().await);
        }

        results.into_iter().find(Result::is_err).unwrap_or(Ok(()))
    }

    pub(crate) async fn are_alive(&self) -> bool {
        for worker in self.workers.lock().await.iter_mut() {
            if !worker.is_alive() {
                return false;
            }
        }
        true
    }

    async fn is_socket_ready(&self) -> bool {
        let result = UnixStream::connect(&self.socket_path).await;
        trace!("checking if worker socket is ready: {result:?}");
        result.is_ok()
    }
}

async fn watch_workers(arbiter: Arbiter, workers: Arc<Workers>) -> Result<()> {
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
                            workers.start_other_workers().await?;
                        }
                    },
                    Err(RecvError::Lagged(_)) => {},
                    Err(RecvError::Closed) => {
                        warn!("error receiving signals");
                        return Err(RecvError::Closed.into());
                    }
                }
            },
            () = tokio::time::sleep(Duration::from_secs(1)), if !INITIAL_WORKER_READY.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the worker unix socket and mark ready once it accepts connections.
                if workers.is_socket_ready().await {
                    info!("worker socket is accepting connections, marked ready for operation");
                    INITIAL_WORKER_READY.store(true, Ordering::Relaxed);
                    workers.start_other_workers().await?;
                }
            },
            () = tokio::time::sleep(Duration::from_secs(5)) => {
                if !workers.are_alive().await {
                    return Err(eyre!("gunicorn has exited unexpectedly"));
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

mod healthcheck {
    use std::sync::Arc;

    use axum::{
        Router,
        body::Body,
        extract::{Request, State},
        http::{StatusCode, header::HOST},
        response::IntoResponse,
        routing::any,
    };

    use crate::{axum::router::wrap_router, db, worker::Workers};

    async fn health_ready(State(workers): State<Arc<Workers>>) -> impl IntoResponse {
        if !workers.are_alive().await || sqlx::query("SELECT 1").execute(db::get()).await.is_err() {
            StatusCode::SERVICE_UNAVAILABLE
        } else {
            let req = Request::builder()
                .method("GET")
                .uri("http://localhost:8000/-/health/ready/")
                .header(HOST, "localhost")
                .body(Body::from(""));
            if let Ok(req) = req
                && let Ok(res) = workers.client.request(req).await
            {
                res.status()
            } else {
                StatusCode::SERVICE_UNAVAILABLE
            }
        }
    }

    async fn health_live(State(workers): State<Arc<Workers>>) -> impl IntoResponse {
        let req = Request::builder()
            .method("GET")
            .uri("http://localhost:8000/-/health/live/")
            .header(HOST, "localhost")
            .body(Body::from(""));
        if let Ok(req) = req
            && let Ok(res) = workers.client.request(req).await
        {
            res.status()
        } else {
            StatusCode::SERVICE_UNAVAILABLE
        }
    }

    async fn fallback() -> impl IntoResponse {
        StatusCode::OK
    }

    pub(super) fn build_router(workers: Arc<Workers>) -> Router {
        wrap_router(
            Router::new()
                .route("/-/heath/ready/", any(health_ready))
                .route("/-/heath/live/", any(health_live))
                .fallback(fallback)
                .with_state(workers),
            true,
        )
    }
}

mod worker_status {
    use std::time::Duration;

    use eyre::Result;
    use nix::unistd::gethostname;
    use uuid::Uuid;

    use crate::{arbiter::Arbiter, authentik_full_version, db};

    async fn keep(arbiter: Arbiter, id: Uuid, hostname: &str, version: &str) -> Result<()> {
        loop {
            tokio::select! {
                () = tokio::time::sleep(Duration::from_secs(30)) => {
                    sqlx::query("
                        INSERT INTO authentik_tasks_workerstatus (id, hostname, version, last_seen)
                            VALUES ($1, $2, $3, NOW())
                            ON CONFLICT (id) DO UPDATE SET last_seen = NOW()
                    ")
                    .bind(id)
                    .bind(hostname)
                    .bind(version)
                    .execute(db::get())
                    .await?;
                },
                () = arbiter.shutdown() => return Ok(()),
            }
        }
    }

    pub(super) async fn run(arbiter: Arbiter) -> Result<()> {
        let id = Uuid::new_v4();
        let raw_hostname = gethostname()?;
        let hostname = raw_hostname.to_string_lossy();
        let version = authentik_full_version();

        loop {
            tokio::select! {
                _ = keep(arbiter.clone(), id, hostname.as_ref(), &version) => {
                    tokio::select! {
                        () = tokio::time::sleep(Duration::from_secs(10)) => {},
                        () = arbiter.shutdown() => return Ok(()),
                    }
                },
                () = arbiter.shutdown() => return Ok(()),
            }
        }
    }
}

pub fn run(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Workers>> {
    let arbiter = tasks.arbiter();

    let workers = Arc::new(Workers::new(temp_dir().join("authentik-worker.sock"))?);

    tasks
        .build_task()
        .name(&format!("{}::watch_workers", module_path!()))
        .spawn(watch_workers(arbiter.clone(), Arc::clone(&workers)))?;

    tasks
        .build_task()
        .name(&format!("{}::worker_status::run", module_path!()))
        .spawn(worker_status::run(arbiter))?;

    if Mode::get() == Mode::Worker {
        let router = healthcheck::build_router(Arc::clone(&workers));

        for addr in config::get().listen.http.iter().copied() {
            server::start_plain(tasks, "worker", router.clone(), addr)?;
        }

        server::start_unix(
            tasks,
            "worker",
            router,
            unix::net::SocketAddr::from_pathname(temp_dir().join("authentik.sock"))?,
        )?;
    }

    Ok(workers)
}
