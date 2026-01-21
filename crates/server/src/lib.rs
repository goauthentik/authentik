use std::{
    net::SocketAddr,
    process::Stdio,
    sync::{Arc, atomic::AtomicBool},
    time::Duration,
};

use argh::FromArgs;
use authentik_config::get_config;
use axum::Router;
use axum_reverse_proxy::ReverseProxy;
use axum_server::Handle;
use eyre::{Result, eyre};
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
use tokio::{
    process::{Child, Command},
    signal::unix::SignalKind,
    sync::{RwLock, broadcast, broadcast::error::RecvError},
    task::JoinSet,
};
use tokio_util::sync::CancellationToken;
use tracing::{info, warn};

struct ServerState {
    gunicorn: Child,
    ready: bool,
    handles: Vec<Handle<SocketAddr>>,
}

impl ServerState {
    fn new(handles: Vec<Handle<SocketAddr>>) -> Result<Self> {
        Ok(Self {
            gunicorn: Command::new("gunicorn")
                .args([
                    "-c",
                    "./lifecycle/gunicorn.conf.py",
                    "authentik.root.asgi:application",
                ])
                // TODO: catch those
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
            ready: false,
            handles,
        })
    }

    async fn shutdown(&mut self, signal: Signal) -> Result<()> {
        if let Some(id) = self.gunicorn.id() {
            kill(Pid::from_raw(id as i32), signal)?;
        }
        self.gunicorn.wait().await?;
        Ok(())
    }

    async fn graceful_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            // TODO: make configurable
            handle.graceful_shutdown(Some(Duration::from_secs(30)));
        }
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&mut self) -> Result<()> {
        for handle in &self.handles {
            handle.shutdown();
        }
        self.shutdown(Signal::SIGINT).await
    }
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub struct Cli {}

async fn watch_gunicorn(
    state_lock: Arc<RwLock<ServerState>>,
    stop: CancellationToken,
    signals_tx: broadcast::Sender<SignalKind>,
) -> Result<()> {
    let mut signals_rx = signals_tx.subscribe();
    loop {
        tokio::select! {
            signal = signals_rx.recv() => {
                match signal {
                    Ok(signal) => {
                        let mut state = state_lock.write().await;
                        if signal == SignalKind::interrupt() {
                            state.fast_shutdown().await?;
                            return Ok(())
                        } else if signal == SignalKind::terminate() {
                            state.graceful_shutdown().await?;
                            return Ok(())
                        } else if signal == SignalKind::user_defined1() {
                            info!("gunicorn is marked ready for operation");
                            state.ready = true;
                        }
                    }
                    Err(RecvError::Lagged(_)) => continue,
                    Err(RecvError::Closed) => {
                        let mut state = state_lock.write().await;
                        state.fast_shutdown().await?;
                        return Ok(());
                    }
                }
            },
            _ = tokio::time::sleep(Duration::from_secs(15)) => {
                let mut state = state_lock.write().await;
                let try_wait = state.gunicorn.try_wait();
                drop(state);
                match try_wait {
                    // Gunicorn has exited. stop as soon as possible
                    Ok(Some(code)) => {
                        signals_tx.send(SignalKind::interrupt())?;
                        return Err(eyre!("gunicorn has exited unexpectedly with status {code}"));
                    }
                    // Gunicorn is still running, or we failed to check the status
                    Ok(None) => continue,
                    Err(err) => {
                        warn!("failed to check the status of gunicorn process, ignoring: {err}");
                        continue;
                    },
                }
            },
            _ = stop.cancelled() => {
                let mut state = state_lock.write().await;
                state.fast_shutdown().await?;
                return Ok(());
            },
        }
    }
}

async fn start_server(addr: SocketAddr, handle: Handle<SocketAddr>) -> Result<()> {
    let connector = UnixSocketConnector::new("/tmp/authentik-core.sock");
    let client = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .pool_max_idle_per_host(4)
        .build(connector);
    let proxy = ReverseProxy::new_with_client("/", "http://localhost:8000", client);
    let app: Router = proxy.into();

    axum_server::bind(addr)
        .handle(handle)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}

pub async fn run(
    _cli: Cli,
    tasks: &mut JoinSet<Result<()>>,
    stop: CancellationToken,
    signals_tx: broadcast::Sender<SignalKind>,
) -> Result<()> {
    let config = get_config();

    let mut handles = Vec::with_capacity(
        config.listen.http.len() + config.listen.https.len() + config.listen.metrics.len(),
    );

    config.listen.http.iter().for_each(|addr| {
        let handle = Handle::new();
        tasks.spawn(start_server(*addr, handle.clone()));
        handles.push(handle);
    });

    let state_lock = Arc::new(RwLock::new(ServerState::new(handles)?));
    tasks.spawn(watch_gunicorn(
        Arc::clone(&state_lock),
        stop.clone(),
        signals_tx,
    ));

    Ok(())
}
