use ak_common::Mode;
use argh::FromArgs;
use eyre::{Result, eyre};
use reqwest::blocking::Client;
use tracing::info;

#[derive(Debug, FromArgs, PartialEq)]
/// Run healthcheck
#[argh(subcommand, name = "healthcheck")]
pub(super) struct Cli {
    #[argh(positional)]
    mode: String,
}

pub(super) fn run(args: &Cli) -> Result<()> {
    let mode: Mode = args.mode.parse()?;
    info!(%mode, "checking health");

    let response = match mode {
        #[cfg(feature = "core")]
        Mode::AllInOne | Mode::Server | Mode::Worker => Client::builder()
            .user_agent("goauthentik.io/healthcheck")
            .unix_socket(crate::server::socket_path())
            .build()?
            .get("http://localhost/-/health/live/")
            .send()?,
        #[cfg(feature = "proxy")]
        Mode::Proxy => Client::builder()
            .user_agent("goauthentik.io/healthcheck")
            .unix_socket(crate::metrics::socket_path())
            .build()?
            .get("http://localhost/outpost.goauthentik.io/ping")
            .send()?,
    };

    if !response.status().is_success() {
        return Err(eyre!("unhealthy status code {}", response.status()));
    }

    info!("successfully checked health");

    Ok(())
}
