use eyre::{Report, eyre};
use std::{process::Stdio, time::Duration};
use tokio::process::Command;
use tokio::task::JoinSet;

use argh::FromArgs;
use eyre::Result;
use tokio::process::Child;

struct GunicornManager {
    child: Child,
}

impl GunicornManager {
    fn start() -> Result<Self> {
        Ok(Self {
            child: Command::new("gunicorn")
                .args([
                    "-c",
                    "./lifecycle/gunicorn.conf.py",
                    "authentik.root.asgi:application",
                ])
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .spawn()?,
        })
    }

    async fn run(&self) -> Result<()> {
        loop {
            tokio::time::sleep(Duration::from_secs(10)).await;
        }
    }

    async fn kill(&mut self) -> Result<()> {
        self.child.kill().await?;
        Ok(())
    }
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server.
#[argh(subcommand, name = "server")]
pub struct Cli {}

#[tokio::main]
pub async fn run(_cli: Cli) -> Result<()> {
    let mut gunicorn = GunicornManager::start()?;

    tokio::time::sleep(Duration::from_secs(30)).await;

    gunicorn.kill().await?;

    Ok(())
}
