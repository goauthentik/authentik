use std::str::FromStr;

use ::tracing::{error, info, trace};
use argh::FromArgs;
use eyre::{Result, eyre};

use crate::{arbiter::Tasks, config::ConfigManager};

mod arbiter;
mod axum;
mod config;
#[cfg(feature = "core")]
mod db;
mod metrics;
mod mode;
#[cfg(feature = "proxy")]
mod proxy;
#[cfg(feature = "core")]
mod server;
mod tokio;
mod tracing;

#[derive(Debug, FromArgs, PartialEq)]
/// The authentication glue you need
struct Cli {
    #[argh(subcommand)]
    command: Command,
}

#[derive(Debug, FromArgs, PartialEq)]
#[argh(subcommand)]
enum Command {
    #[cfg(feature = "core")]
    Server(server::Cli),
    #[cfg(feature = "proxy")]
    Proxy(proxy::Cli),
}

fn install_sentry() -> sentry::ClientInitGuard {
    trace!("setting up sentry");
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

fn main() -> Result<()> {
    let tracing_crude = tracing::install_crude();
    info!(version = env!("CARGO_PKG_VERSION"), "authentik is starting");

    trace!("installing error formatting");
    color_eyre::install()?;

    trace!("installing rustls crypto provider");
    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .expect("Failed to install rustls provider");

    let cli: Cli = argh::from_env();

    match &cli.command {
        #[cfg(feature = "core")]
        Command::Server(_) => mode::set(mode::Mode::Server),
        #[cfg(feature = "proxy")]
        Command::Proxy(_) => mode::set(mode::Mode::Proxy),
    };

    #[cfg(feature = "core")]
    if mode::get() == mode::Mode::Server {
        if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
            let mut dir = std::env::temp_dir();
            dir.push("authentik_prometheus_tmp");
            std::fs::create_dir_all(&dir)?;
            // SAFETY: there is only one thread at this point, so this is safe.
            unsafe {
                std::env::set_var("PROMETHEUS_MULTIPROC_DIR", dir);
            }
            trace!(
                env = std::env::var("PROMETHEUS_MULTIPROC_DIR").unwrap_or_default(),
                "setting PROMETHEUS_MULTIPROC_DIR"
            );
        } else {
            trace!("PROMETHEUS_MULTIPROC_DIR already set");
        }

        trace!("initializing Python");
        pyo3::Python::initialize();
        trace!("Python initialized");
    }

    ::tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?
        .block_on(async {
            let mut tasks = Tasks::new()?;

            ConfigManager::init(&mut tasks).await?;

            tracing::install()?;
            drop(tracing_crude);

            let _sentry = if config::get().error_reporting.enabled {
                Some(install_sentry())
            } else {
                None
            };

            metrics::run(&mut tasks).await?;

            #[cfg(feature = "core")]
            if mode::get() == mode::Mode::Server {
                db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::Server(args) => {
                    server::run(args, &mut tasks).await?;
                }
                #[cfg(feature = "proxy")]
                Command::Proxy(_args) => todo!(),
            };

            let errors = tasks.run().await;

            if !errors.is_empty() {
                error!("authentik encountered errors: {:?}", errors);
                Err(eyre!("Errors encountered: {:?}", errors))
            } else {
                info!("authentik exiting");
                Ok(())
            }
        })
}
