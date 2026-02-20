use std::str::FromStr;

use ::tokio::sync::broadcast;
use argh::FromArgs;
use eyre::{Result, eyre};
use pyo3::Python;

use crate::{arbiter::Tasks, config::ConfigManager};

mod arbiter;
mod axum;
mod config;
#[cfg(feature = "server")]
mod db;
mod metrics;
#[cfg(any(feature = "server", feature = "proxy"))]
mod proxy;
#[cfg(feature = "server")]
mod server;
mod tokio;

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
    #[cfg(feature = "proxy")]
    Proxy(proxy::Cli),
}

fn install_tracing() -> Result<()> {
    use tracing_error::ErrorLayer;
    use tracing_subscriber::{filter::EnvFilter, fmt, prelude::*};

    let config = config::get();

    let default = format!("{},postgres=info", config.log_level);
    let filter_layer = EnvFilter::builder()
        .with_default_directive(config.log_level.parse().expect("Invalid log_level"))
        .parse(default)?;
    let filter_layer = if !config.log.rust_log.is_empty() {
        filter_layer.add_directive(config.log.rust_log.join(",").parse()?)
    } else {
        filter_layer
    };

    // TODO: refine this to match Python
    if config.debug {
        let console_layer = console_subscriber::ConsoleLayer::builder()
            .server_addr(config.listen.debug)
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

fn install_sentry() -> sentry::ClientInitGuard {
    let config = config::get();
    sentry::init(sentry::ClientOptions {
        // TODO: refine a bit more
        dsn: config
            .error_reporting
            .sentry_dsn
            .clone()
            .map(|dsn| sentry::types::Dsn::from_str(&dsn).expect("Failed to create sentry DSN")),
        environment: Some(config.error_reporting.environment.clone().into()),
        attach_stacktrace: true,
        send_default_pii: config.error_reporting.send_pii,
        sample_rate: config.error_reporting.sample_rate,
        traces_sample_rate: config.error_reporting.sample_rate,
        ..sentry::ClientOptions::default()
    })
}

#[::tokio::main(crate = "::tokio")]
async fn main() -> Result<()> {
    color_eyre::install()?;

    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .expect("Failed to install rustls provider");

    let cli: Cli = argh::from_env();

    #[cfg(feature = "server")]
    {
        if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
            let mut dir = std::env::temp_dir();
            dir.push("authentik_prometheus_tmp");
            std::fs::create_dir_all(&dir)?;
            // SAFETY: there is only one thread at this point, so this is safe.
            unsafe {
                std::env::set_var("PROMETHEUS_MULTIPROC_DIR", dir);
            }
        }

        Python::initialize();
    }

    ::tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let mut tasks = Tasks::new()?;

            let (config_changed_tx, config_changed_rx) = broadcast::channel(100);
            ConfigManager::init(&mut tasks, config_changed_tx.clone()).await?;

            install_tracing()?;

            let _sentry = if config::get().error_reporting.enabled {
                Some(install_sentry())
            } else {
                None
            };

            #[cfg(feature = "server")]
            {
                db::init(&mut tasks, config_changed_rx).await?;
            }

            match cli.command {
                #[cfg(feature = "server")]
                Command::Server(args) => {
                    server::run(args, &mut tasks).await?;
                }
                #[cfg(feature = "proxy")]
                Command::Proxy(_args) => todo!(),
            };

            let errors = tasks.run().await;

            if !errors.is_empty() {
                Err(eyre!("Errors encountered: {:?}", errors))
            } else {
                Ok(())
            }
        })
}
