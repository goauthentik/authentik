use std::process::Stdio;
use tracing::warn;

use eyre::Result;
use nix::{
    sys::signal::{Signal, kill},
    unistd::Pid,
};
use tokio::process::{Child, Command};

pub(super) struct Gunicorn(Child);

impl Gunicorn {
    pub(super) fn new() -> Result<Self> {
        Ok(Self(
            Command::new("gunicorn")
                .args([
                    "-c",
                    "./lifecycle/gunicorn.conf.py",
                    "authentik.root.asgi:application",
                ])
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
        ))
    }

    async fn shutdown(&mut self, signal: Signal) -> Result<()> {
        if let Some(id) = self.0.id() {
            kill(Pid::from_raw(id as i32), signal)?;
        }
        self.0.wait().await?;
        Ok(())
    }

    pub(super) async fn graceful_shutdown(&mut self) -> Result<()> {
        self.shutdown(Signal::SIGTERM).await
    }

    pub(super) async fn fast_shutdown(&mut self) -> Result<()> {
        self.shutdown(Signal::SIGINT).await
    }

    pub(super) async fn is_alive(&mut self) -> bool {
        let try_wait = self.0.try_wait();
        match try_wait {
            Ok(Some(code)) => {
                warn!("gunicorn has exited unexpectedly with status {code}");
                false
            }
            Ok(None) => true,
            Err(err) => {
                warn!("failed to check the status of gunicorn process, ignoring: {err}");
                true
            }
        }
    }
}

