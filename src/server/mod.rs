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

use ak_common::{Arbiter, Event, Tasks, config};
use arc_swap::ArcSwapOption;
use argh::FromArgs;
use axum::{Router, body::Body, extract::Request, routing::any};
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
    time::{Duration, Instant, interval},
};
use tower::ServiceExt;
use tracing::{info, trace, warn};

use crate::worker::Workers;

mod core;
mod r#static;
mod tls;

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct Cli {}

pub(super) static GUNICORN_READY: AtomicBool = AtomicBool::new(false);

pub(crate) fn socket_path() -> PathBuf {
    temp_dir().join("authentik.sock")
}

pub(crate) struct Server {
    gunicorn: Mutex<Child>,
    socket_path: PathBuf,
    pub(crate) client: Client<UnixSocketConnector<PathBuf>, Body>,
    pub(crate) workers: ArcSwapOption<Workers>,
}

impl Server {
    async fn new(socket_path: PathBuf) -> Result<Self> {
        info!("starting server");

        let gunicorn = Command::new("gunicorn")
            .args([
                "--bind",
                &format!("unix://{}", socket_path.display()),
                "-c",
                "./lifecycle/gunicorn.conf.py",
                "authentik.root.asgi:application",
            ])
            .kill_on_drop(true)
            .stdin(Stdio::null())
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;

        let client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_mins(1))
            .set_host(false)
            .build(UnixSocketConnector::new(socket_path.clone()));

        Ok(Self {
            gunicorn: Mutex::new(gunicorn),
            client,
            socket_path,
            workers: ArcSwapOption::empty(),
        })
    }

    async fn shutdown(&self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to server"
        );
        let mut gunicorn = self.gunicorn.lock().await;
        if let Some(id) = gunicorn.id() {
            kill(Pid::from_raw(id.cast_signed()), signal)?;
        }
        gunicorn.wait().await?;
        drop(gunicorn);
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        info!("gracefully shutting down server");
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&self) -> Result<()> {
        info!("gracefully shutting down server");
        self.shutdown(Signal::SIGINT).await
    }

    async fn is_alive(&self) -> bool {
        let try_wait = self.gunicorn.lock().await.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!(?code, "server has exited");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!(
                    ?err,
                    "failed to check the status of server process, ignoring"
                );
                true
            }
        }
    }

    async fn is_socket_ready(&self) -> bool {
        let result = UnixStream::connect(&self.socket_path).await;
        trace!(?result, "checking if server socket is ready");
        result.is_ok()
    }
}

async fn watch_server(arbiter: Arbiter, server: Arc<Server>) -> Result<()> {
    info!("starting server watcher");
    let mut events_rx = arbiter.events_subscribe();
    let mut check_interval = interval(Duration::from_secs(5));
    let mut start_interval = interval(Duration::from_secs(1));

    loop {
        tokio::select! {
            Ok(Event::Signal(signal)) = events_rx.recv() => {
                if signal == SignalKind::user_defined1() {
                    info!("server notified us ready, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                }
            },
            _ = start_interval.tick(), if !GUNICORN_READY.load(Ordering::Relaxed) => {
                if server.is_socket_ready().await {
                    info!("server socket is accepting connections, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                }
            },
            _ = check_interval.tick() => {
                if !server.is_alive().await {
                    return Err(eyre!("the server has exited unexpectedly"));
                }
            },
            () = arbiter.fast_shutdown() => {
                server.fast_shutdown().await?;
                return Ok(());
            }
            () = arbiter.graceful_shutdown() => {
                server.graceful_shutdown().await?;
                return Ok(());
            }
        }
    }
}

fn build_router(server: Arc<Server>) -> Router {
    let core_router = core::build_router(server);
    // let proxy_router = Router::new();

    metrics::describe_histogram!(
        "authentik_main_request_duration",
        metrics::Unit::Seconds,
        "API request latencies in seconds"
    );

    Router::new().fallback(any(async |request: Request<Body>| {
        let now = Instant::now();

        let res = core_router.oneshot(request).await;
        metrics::histogram!("authentik_main_request_duration", "dest" => "core")
            .record(now.elapsed());
        res
    }))
}

pub(crate) async fn start(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Server>> {
    let arbiter = tasks.arbiter();

    let server = Arc::new(Server::new(temp_dir().join("authentik-gunicorn.sock")).await?);

    tasks
        .build_task()
        .name(&format!("{}::watch_server", module_path!()))
        .spawn(watch_server(arbiter.clone(), Arc::clone(&server)))?;

    let router = build_router(Arc::clone(&server));

    for addr in config::get().listen.http.iter().copied() {
        ak_axum::server::start_plain(tasks, "server", router.clone(), addr)?;
    }

    let tls_config = tls::make_initial_tls_config()?;
    for addr in config::get().listen.https.iter().copied() {
        ak_axum::server::start_tls(tasks, "server", router.clone(), addr, tls_config.clone())?;
    }
    tasks
        .build_task()
        .name(&format!("{}::tls::watch_tls_config", module_path!()))
        .spawn(tls::watch_tls_config(arbiter, tls_config))?;

    ak_axum::server::start_unix(
        tasks,
        "server",
        router,
        unix::net::SocketAddr::from_pathname(socket_path())?,
    )?;

    Ok(server)
}
