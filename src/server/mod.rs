use std::{env::temp_dir, path::PathBuf, process::Stdio, sync::Arc, time::Duration};

use argh::FromArgs;
use axum::body::Body;
use eyre::{Result, eyre};
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use tracing::{info, trace, warn};

use crate::arbiter::{Arbiter, Tasks};

#[derive(Debug, Default, FromArgs, PartialEq, Eq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub struct Cli {}

pub(crate) fn socket_path() -> PathBuf {
    temp_dir().join("authentik.sock")
}

pub struct Server {
    server: Mutex<Child>,
    pub(crate) metrics_client: Client<UnixSocketConnector<PathBuf>, Body>,
}

impl Server {
    fn new() -> Result<Self> {
        info!("starting server");

        let server = if which::which("authentik-server").is_ok() {
            Command::new("authentik-server")
                .kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?
        } else {
            Command::new("go")
                .args(["run", "./cmd/server"])
                .kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?
        };

        let metrics_client = Client::builder(TokioExecutor::new())
            .pool_idle_timeout(Duration::from_secs(60))
            .set_host(false)
            .build(UnixSocketConnector::new(
                temp_dir().join("authentik-server-metrics.sock"),
            ));

        Ok(Self {
            server: Mutex::new(server),
            metrics_client,
        })
    }

    async fn shutdown(&self, signal: Signal) -> Result<()> {
        trace!(
            signal = signal.as_str(),
            "sending shutdown signal to server"
        );
        let mut server = self.server.lock().await;
        if let Some(id) = server.id() {
            kill(Pid::from_raw(id.cast_signed()), signal)?;
        }
        server.wait().await?;
        drop(server);
        Ok(())
    }

    async fn graceful_shutdown(&self) -> Result<()> {
        info!("gracefully shutting down server");
        self.shutdown(Signal::SIGTERM).await
    }

    async fn fast_shutdown(&self) -> Result<()> {
        info!("immediately shutting down server");
        self.shutdown(Signal::SIGINT).await
    }

    async fn is_alive(&self) -> bool {
        let try_wait = self.server.lock().await.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!("server has exited with status {code}");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!("failed to check the status of server process, ignoring: {err}");
                true
            }
        }
    }
}

async fn watch_server(arbiter: Arbiter, server: Arc<Server>) -> Result<()> {
    info!("starting server watcher");
    loop {
        tokio::select! {
            () = tokio::time::sleep(Duration::from_secs(5)) => {
                if !server.is_alive().await {
                    return Err(eyre!("server has exited unexpectedly"));
                }
            }
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

pub fn run(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Server>> {
    let arbiter = tasks.arbiter();

    let server = Arc::new(Server::new()?);

    tasks
        .build_task()
        .name(&format!("{}::watch_server", module_path!()))
        .spawn(watch_server(arbiter, Arc::clone(&server)))?;

    Ok(server)
}
