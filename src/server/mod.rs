use std::{
    env,
    path::PathBuf,
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};

use arc_swap::ArcSwapOption;
use argh::FromArgs;
use axum::{Router, body::Body, extract::Request, routing::any};
use axum_server::Handle;
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
    time::Instant,
};
use tower::ServiceExt;
use tracing::{info, trace, warn};

use crate::{
    arbiter::{Arbiter, Tasks},
    config,
    worker::Workers,
};

pub(super) static GUNICORN_READY: AtomicBool = AtomicBool::new(false);

pub(crate) mod core;
mod plain;
mod r#static;
mod tls;

#[derive(Debug, Default, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub(super) struct Cli {}

pub(crate) struct Server {
    gunicorn: Mutex<Child>,
    socket_path: PathBuf,
    pub(crate) client: Client<UnixSocketConnector<PathBuf>, Body>,
    pub(crate) workers: ArcSwapOption<Workers>,
}

impl Server {
    fn new(socket_path: PathBuf) -> Result<Self> {
        info!("starting gunicorn");
        let gunicorn = Command::new("gunicorn")
            .args([
                "--bind",
                &format!("unix://{}", socket_path.display()),
                "-c",
                "./lifecycle/gunicorn.conf.py",
                "authentik.root.asgi:application",
            ])
            .kill_on_drop(true)
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;

        let client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_secs(60))
            .set_host(false)
            .build(UnixSocketConnector::new(socket_path.clone()));

        Ok(Self {
            gunicorn: Mutex::new(gunicorn),
            socket_path,
            client,
            workers: ArcSwapOption::empty(),
        })
    }

    async fn shutdown(&self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to gunicorn"
        );
        if let Some(id) = self.gunicorn.lock().await.id() {
            kill(Pid::from_raw(id.cast_signed()), signal)?;
        }
        self.gunicorn.lock().await.wait().await?;
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        info!("gracefully shutting down gunicorn");
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&self) -> Result<()> {
        info!("immediately shutting down gunicorn");
        self.shutdown(Signal::SIGINT).await
    }

    async fn is_alive(&self) -> bool {
        let try_wait = self.gunicorn.lock().await.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!("gunicorn has exited with status {code}");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!("failed to check the status of gunicorn process, ignoring: {err}");
                true
            }
        }
    }

    async fn is_socket_ready(&self) -> bool {
        let result = UnixStream::connect(&self.socket_path).await;
        trace!("checking if gunicorn is ready: {result:?}");
        result.is_ok()
    }
}

async fn watch_server(arbiter: Arbiter, server: Arc<Server>) -> Result<()> {
    info!("starting server watcher");
    let mut signals_rx = arbiter.signals_subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        if signal == SignalKind::user_defined1() {
                            info!("gunicorn notified us ready, marked ready for operation");
                            GUNICORN_READY.store(true, Ordering::Relaxed);
                            arbiter.mark_gunicorn_ready();
                        }
                    },
                    Err(RecvError::Lagged(_)) => {},
                    Err(RecvError::Closed) => {
                        warn!("error receiving signals");
                        return Err(RecvError::Closed.into());
                    }
                }
            },
            () = tokio::time::sleep(Duration::from_secs(1)), if !GUNICORN_READY.load(Ordering::Relaxed) => {
                // On some platforms the SIGUSR1 can be missed.
                // Fall back to probing the gunicorn unix socket and mark ready once it accepts connections.
                if server.is_socket_ready().await {
                    info!("gunicorn socket is accepting connections, marked ready for operation");
                    GUNICORN_READY.store(true, Ordering::Relaxed);
                    arbiter.mark_gunicorn_ready();
                }
            },
            () = tokio::time::sleep(Duration::from_secs(5)) => {
                if !server.is_alive().await {
                    return Err(eyre!("gunicorn has exited unexpectedly"));
                }
            },
            () = arbiter.fast_shutdown() => {
                server.fast_shutdown().await?;
                return Ok(());
            },
            () = arbiter.graceful_shutdown() => {
                server.graceful_shutdown().await?;
                return Ok(());
            },
        }
    }
}

fn build_router(server: Arc<Server>) -> Router {
    let core_router = core::build_router(server);
    let proxy_router: Option<Router> = None;

    Router::new().fallback(any(|request: Request<Body>| async move {
        metrics::describe_histogram!(
            "authentik_main_request_duration",
            metrics::Unit::Seconds,
            "API request latencies in seconds"
        );
        let now = Instant::now();
        if let Some(proxy_router) = proxy_router
            && crate::proxy::can_handle(&request)
        {
            let res = proxy_router.oneshot(request).await;
            metrics::histogram!("authentik_main_request_duration", "dest" => "embedded_outpost")
                .record(now.elapsed());
            res
        } else {
            let res = core_router.oneshot(request).await;
            metrics::histogram!("authentik_main_request_duration", "dest" => "core")
                .record(now.elapsed());
            res
        }
    }))
}

pub(super) async fn run(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Server>> {
    let config = config::get();
    let arbiter = tasks.arbiter();

    let server = Arc::new(Server::new(
        env::temp_dir().join("authentik-gunicorn.sock"),
    )?);

    let router = build_router(server.clone());
    let tls_config = tls::make_initial_tls_config()?;

    tasks
        .build_task()
        .name(&format!("{}::tls::watch_tls_config", module_path!(),))
        .spawn(tls::watch_tls_config(arbiter.clone(), tls_config.clone()))?;

    for addr in config.listen.http.iter().copied() {
        let handle = Handle::new();
        arbiter.add_handle(handle.clone()).await;
        tasks
            .build_task()
            .name(&format!(
                "{}::plain::run_server_plain({})",
                module_path!(),
                addr
            ))
            .spawn(plain::run_server_plain(router.clone(), addr, handle))?;
    }

    for addr in config.listen.https.iter().copied() {
        let handle = Handle::new();
        arbiter.add_handle(handle.clone()).await;
        tasks
            .build_task()
            .name(&format!(
                "{}::tls::run_server_tls({})",
                module_path!(),
                addr
            ))
            .spawn(tls::run_server_tls(
                router.clone(),
                addr,
                tls_config.clone(),
                handle,
            ))?;
    }

    tasks
        .build_task()
        .name(&format!("{}::watch_server", module_path!()))
        .spawn(watch_server(arbiter, server.clone()))?;

    Ok(server)
}
