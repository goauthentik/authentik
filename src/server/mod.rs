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
use tokio::{
    process::{Child, Command},
    sync::Mutex,
};
use tracing::{info, warn};

use crate::{
    arbiter::{Arbiter, Tasks},
    config,
};

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
    async fn new() -> Result<Self> {
        info!("starting server");

        let server = if config::get().debug && which::which("authentik-server").is_err() {
            let build_status = Command::new("go")
                .args(["build", "-o", "authentik-server", "./cmd/server"])
                .stdin(Stdio::null())
                .status()
                .await?;
            if !build_status.success() {
                return Err(eyre!("golang server failed to compile"));
            }
            Command::new("./authentik-server")
                .kill_on_drop(true)
                .stdin(Stdio::null())
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?
        } else {
            Command::new("authentik-server")
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

    async fn shutdown(&self) -> Result<()> {
        info!("shutting down server");
        let mut server = self.server.lock().await;
        if let Some(id) = server.id() {
            kill(Pid::from_raw(id.cast_signed()), Signal::SIGINT)?;
        }
        tokio::time::timeout(Duration::from_secs(1), server.wait()).await??;
        Ok(())
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
            () = arbiter.shutdown() => {
                server.shutdown().await?;
                return Ok(());
            },
        }
    }
}

pub async fn run(_cli: Cli, tasks: &mut Tasks) -> Result<Arc<Server>> {
    let arbiter = tasks.arbiter();

    let server = Arc::new(Server::new().await?);

    tasks
        .build_task()
        .name(&format!("{}::watch_server", module_path!()))
        .spawn(watch_server(arbiter, Arc::clone(&server)))?;

    Ok(server)
}
