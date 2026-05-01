use std::sync::atomic::{AtomicUsize, Ordering};

#[cfg(feature = "core")]
use ak_common::db;
use ak_common::{Mode, Tasks, authentik_full_version, config, tls, tracing as ak_tracing};
use argh::FromArgs;
use eyre::{Result, eyre};
use tracing::{error, info, trace};

mod metrics;
#[cfg(feature = "core")]
mod server;
#[cfg(feature = "core")]
mod worker;

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
    Worker(worker::Cli),
}

fn main() -> Result<()> {
    let tracing_crude = ak_tracing::install_crude();
    info!(version = authentik_full_version(), "authentik is starting");

    let cli: Cli = argh::from_env();

    match &cli.command {
        #[cfg(feature = "core")]
        Command::Worker(_) => Mode::set(Mode::Worker)?,
    }

    trace!("installing error formatting");
    color_eyre::install()?;

    #[cfg(feature = "core")]
    if Mode::is_core() {
        trace!("initializing Python");
        pyo3::Python::initialize();
        trace!("Python initialized");
    }

    config::init()?;
    tls::init()?;

    let _sentry = ak_tracing::sentry::install()?;
    ak_tracing::install()?;
    drop(tracing_crude);

    tokio::runtime::Builder::new_multi_thread()
        .thread_name_fn(|| {
            static ATOMIC_ID: AtomicUsize = AtomicUsize::new(0);
            let id = ATOMIC_ID.fetch_add(1, Ordering::SeqCst);
            format!("tokio-{id}")
        })
        .enable_all()
        .build()?
        .block_on(async {
            let mut tasks = Tasks::new()?;

            config::start(&mut tasks)?;

            let metrics = metrics::start(&mut tasks)?;

            #[cfg(feature = "core")]
            if Mode::get() == Mode::AllInOne || Mode::get() == Mode::Worker {
                db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::Worker(args) => {
                    let workers = worker::start(args, &mut tasks)?;
                    metrics.workers.store(Some(workers));
                }
            }

            let errors = tasks.run().await;

            Mode::cleanup();

            if errors.is_empty() {
                info!("authentik exiting");
                Ok(())
            } else {
                error!(err = ?errors, "authentik encountered errors");
                Err(eyre!("Errors encountered: {:?}", errors))
            }
        })
}
