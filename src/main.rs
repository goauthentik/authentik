use std::{
    process::exit,
    sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    },
};

use ::tracing::{error, info, trace};
use argh::FromArgs;
use eyre::{Result, eyre};

use crate::{arbiter::Tasks, config::ConfigManager, mode::Mode};

mod arbiter;
mod axum;
#[cfg(feature = "core")]
mod brands;
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
#[cfg(feature = "core")]
mod worker;

const VERSION: &str = env!("CARGO_PKG_VERSION");

pub(crate) fn authentik_build_hash(fallback: Option<String>) -> String {
    std::env::var("GIT_BUILD_HASH").unwrap_or_else(|_| fallback.unwrap_or_default())
}

pub(crate) fn authentik_full_version() -> String {
    let build_hash = authentik_build_hash(None);
    if build_hash.is_empty() {
        VERSION.to_owned()
    } else {
        format!("{VERSION}+{build_hash}")
    }
}

pub(crate) fn authentik_user_agent() -> String {
    format!("authentik@{}", authentik_full_version())
}

#[derive(Debug, FromArgs, PartialEq)]
/// The authentication glue you need.
struct Cli {
    #[argh(subcommand)]
    command: Command,
}

#[derive(Debug, FromArgs, PartialEq)]
#[argh(subcommand)]
enum Command {
    #[cfg(feature = "core")]
    AllInOne(AllInOne),
    #[cfg(feature = "core")]
    Server(server::Cli),
    #[cfg(feature = "core")]
    Worker(worker::Cli),
    #[cfg(feature = "proxy")]
    Proxy(proxy::Cli),
    #[cfg(feature = "core")]
    Manage(Manage),
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run the authentik server and worker.
#[argh(subcommand, name = "allinone")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
struct AllInOne {}

#[derive(Debug, FromArgs, PartialEq)]
/// authentik django's management command.
#[argh(subcommand, name = "manage")]
struct Manage {
    #[argh(positional, greedy)]
    args: Vec<String>,
}

fn main() -> Result<()> {
    let tracing_crude = tracing::install_crude();
    info!(version = env!("CARGO_PKG_VERSION"), "authentik is starting");

    let cli: Cli = argh::from_env();

    match &cli.command {
        #[cfg(feature = "core")]
        Command::AllInOne(_) => Mode::set(Mode::AllInOne)?,
        #[cfg(feature = "core")]
        Command::Server(_) => Mode::set(Mode::Server)?,
        #[cfg(feature = "core")]
        Command::Worker(_) => Mode::set(Mode::Worker)?,
        #[cfg(feature = "proxy")]
        Command::Proxy(_) => Mode::set(Mode::Proxy)?,
        #[cfg(feature = "core")]
        Command::Manage(args) => {
            let mut process = std::process::Command::new("python")
                .args(["-m", "manage"])
                .args(&args.args)
                .spawn()?;
            let status = process.wait()?;
            if let Some(code) = status.code() {
                exit(code);
            }
            return Ok(());
        }
    }

    trace!("installing error formatting");
    color_eyre::install()?;

    trace!("installing rustls crypto provider");
    #[expect(
        clippy::unwrap_in_result,
        reason = "result type does not implement Error"
    )]
    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .expect("Failed to install rustls provider");

    #[cfg(feature = "core")]
    if Mode::is_core() {
        if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
            let dir = std::env::temp_dir().join("authentik_prometheus_tmp");
            std::fs::create_dir_all(&dir)?;
            #[expect(unsafe_code, reason = "see safety comment below")]
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

    ConfigManager::init()?;

    let _sentry = config::get()
        .error_reporting
        .enabled
        .then(tracing::sentry::install);

    tracing::install()?;
    drop(tracing_crude);

    ::tokio::runtime::Builder::new_multi_thread()
        .thread_name_fn(|| {
            static ATOMIC_ID: AtomicUsize = AtomicUsize::new(0);
            let id = ATOMIC_ID.fetch_add(1, Ordering::SeqCst);
            format!("tokio-{id}")
        })
        .enable_all()
        .build()?
        .block_on(async {
            let mut tasks = Tasks::new()?;

            ConfigManager::run(&mut tasks)?;

            let metrics = metrics::run(&mut tasks)?;

            #[cfg(feature = "core")]
            if Mode::is_core() {
                db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::AllInOne(_) => {
                    let workers = worker::run(worker::Cli::default(), &mut tasks)?;
                    metrics.workers.store(Some(Arc::clone(&workers)));
                    let server = server::run(server::Cli::default(), &mut tasks)?;
                    server.workers.store(Some(workers));
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Server(args) => {
                    let server = server::run(args, &mut tasks)?;
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Worker(args) => {
                    let workers = worker::run(args, &mut tasks)?;
                    metrics.workers.store(Some(workers));
                }
                #[cfg(feature = "proxy")]
                Command::Proxy(args) => proxy::run(args, &mut tasks)?,
                #[cfg(feature = "core")]
                Command::Manage(_) => unreachable!(),
            }

            let errors = tasks.run().await;

            if errors.is_empty() {
                info!("authentik exiting");
                Ok(())
            } else {
                error!("authentik encountered errors: {:?}", errors);
                Err(eyre!("Errors encountered: {:?}", errors))
            }
        })
}
