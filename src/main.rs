use std::str::FromStr;

use ::tokio::{fs, sync::broadcast};
use argh::FromArgs;
use eyre::{Result, eyre};
use pyo3::Python;

use crate::{
    arbiter::Tasks,
    config::{ConfigManager, get_config},
};

mod arbiter;
mod axum;
mod config;
#[cfg(any(feature = "server", feature = "proxy"))]
mod db;
mod metrics;
#[cfg(any(feature = "server", feature = "proxy"))]
mod proxy;
#[cfg(feature = "server")]
mod server;
mod tokio;
mod worker;

#[derive(Debug, FromArgs, PartialEq)]
/// The authentication glue you need
struct Cli {
    #[argh(subcommand)]
    command: Command,
}

#[derive(Debug, FromArgs, PartialEq)]
#[argh(subcommand)]
enum Command {
    #[cfg(feature = "server")]
    Server(server::Cli),
    #[cfg(feature = "worker")]
    Worker(worker::Cli),
}

async fn install_tracing() -> Result<()> {
    use tracing_error::ErrorLayer;
    use tracing_subscriber::{filter::EnvFilter, fmt, prelude::*};

    let default = format!("{},postgres=info", get_config().await.log_level);
    let filter_layer = EnvFilter::builder()
        .with_default_directive(
            get_config()
                .await
                .log_level
                .parse()
                .expect("Invalid log_level"),
        )
        .parse(default)?;
    let filter_layer = if !get_config().await.log.rust_log.is_empty() {
        filter_layer.add_directive(get_config().await.log.rust_log.join(",").parse()?)
    } else {
        filter_layer
    };

    if get_config().await.debug {
        let console_layer = console_subscriber::ConsoleLayer::builder()
            .server_addr(get_config().await.listen.debug)
            .spawn();
        tracing_subscriber::registry()
            .with(console_layer)
            .with(filter_layer)
            .with(
                fmt::layer()
                    .compact()
                    .with_thread_ids(true)
                    .with_thread_names(true)
                    .with_file(true)
                    .with_line_number(true)
                    .with_writer(std::io::stderr),
            )
            .with(ErrorLayer::default())
            .with(sentry::integrations::tracing::layer())
            .init();
    } else {
        tracing_subscriber::registry()
            .with(filter_layer)
            .with(
                fmt::layer()
                    .json()
                    .with_thread_ids(true)
                    .with_thread_names(true)
                    .with_file(true)
                    .with_line_number(true)
                    .with_writer(std::io::stderr),
            )
            .with(ErrorLayer::default())
            .with(sentry::integrations::tracing::layer())
            .init();
    }

    Ok(())
}

#[::tokio::main(crate = "::tokio")]
async fn main() -> Result<()> {
    color_eyre::install()?;

    let mut tasks = Tasks::new()?;

    let (config_changed_tx, config_changed_rx) = broadcast::channel(100);
    ConfigManager::init(&mut tasks, config_changed_tx.clone()).await?;

    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .expect("Failed to install rustls provider");

    let _sentry = if get_config().await.error_reporting.enabled {
        Some(sentry::init(sentry::ClientOptions {
            // TODO: refine a bit more
            dsn: get_config()
                .await
                .error_reporting
                .sentry_dsn
                .clone()
                .map(|dsn| {
                    sentry::types::Dsn::from_str(&dsn).expect("Failed to create sentry DSN")
                }),
            environment: Some(
                get_config()
                    .await
                    .error_reporting
                    .environment
                    .clone()
                    .into(),
            ),
            attach_stacktrace: true,
            send_default_pii: get_config().await.error_reporting.send_pii,
            sample_rate: get_config().await.error_reporting.sample_rate,
            traces_sample_rate: get_config().await.error_reporting.sample_rate,
            ..sentry::ClientOptions::default()
        }))
    } else {
        None
    };

    install_tracing().await?;
    let cli: Cli = argh::from_env();

    #[cfg(any(feature = "server", feature = "worker"))]
    {
        if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
            let mut dir = std::env::temp_dir();
            dir.push("authentik_prometheus_tmp");
            fs::create_dir_all(&dir).await?;
            // SAFETY: there is only one thread at this point, so this is safe.
            unsafe {
                std::env::set_var("PROMETHEUS_MULTIPROC_DIR", dir);
            }
        }

        db::init(&mut tasks, config_changed_rx).await?;

        Python::initialize();
    }

    match cli.command {
        #[cfg(feature = "server")]
        Command::Server(args) => {
            server::run(args, &mut tasks).await?;
        }
        #[cfg(feature = "worker")]
        Command::Worker(_args) => todo!(),
    };

    let errors = tasks.run().await;

    if !errors.is_empty() {
        Err(eyre!("Errors encountered: {:?}", errors))
    } else {
        Ok(())
    }
}
