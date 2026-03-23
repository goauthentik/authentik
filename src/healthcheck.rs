use std::{env::temp_dir, time::Duration};

use argh::FromArgs;
use axum::{
    body::Body,
    http::{Request, header::HOST},
};
use eyre::{Result, eyre};
use hyper_unix_socket::UnixSocketConnector;
use hyper_util::{client::legacy::Client, rt::TokioExecutor};

use crate::{
    config::{self, ConfigManager},
    mode::Mode,
};

#[derive(Clone, Debug, FromArgs, PartialEq, Eq)]
/// Check authentik's health
#[argh(subcommand, name = "healthcheck")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub struct Cli {}

#[tokio::main]
pub async fn run(_cli: Cli) -> Result<()> {
    Mode::load()?;

    ConfigManager::init()?;

    match Mode::get() {
        #[cfg(feature = "core")]
        Mode::AllInOne => {
            server_healthcheck().await?;
            worker_healthcheck().await?;
            Ok(())
        }
        #[cfg(feature = "core")]
        Mode::Server => server_healthcheck().await,
        #[cfg(feature = "core")]
        Mode::Worker => worker_healthcheck().await,
    }
}

#[cfg(feature = "core")]
async fn server_healthcheck() -> Result<()> {
    let client: Client<_, Body> = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .set_host(false)
        .build(UnixSocketConnector::new(temp_dir().join("authentik.sock")));

    let request = Request::builder()
        .method("GET")
        .uri(format!(
            "http://localhost{}-/health/live/",
            config::get().web.path
        ))
        .header(HOST, "localhost")
        .body(Body::from(""))?;

    let res = client.request(request).await?;
    if !res.status().is_success() {
        return Err(eyre!("unhealthy status code"));
    }

    Ok(())
}

#[cfg(feature = "core")]
async fn worker_healthcheck() -> Result<()> {
    let client: Client<_, Body> = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(60))
        .set_host(false)
        .build(UnixSocketConnector::new(temp_dir().join("authentik.sock")));

    let request = Request::builder()
        .method("GET")
        .uri(format!(
            "http://localhost{}-/health/live/",
            config::get().web.path
        ))
        .header(HOST, "localhost")
        .body(Body::from(""))?;

    let res = client.request(request).await?;
    if !res.status().is_success() {
        return Err(eyre!("unhealthy status code"));
    }

    Ok(())
}
