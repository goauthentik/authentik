use std::{
    process::exit,
    sync::atomic::{AtomicUsize, Ordering},
};

use argh::FromArgs;
use authentik::{arbiter::Tasks, config::ConfigManager, mode::Mode};
use eyre::{Result, eyre};
use tracing::{error, info, trace};

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
    Server(authentik::server::Cli),
    #[cfg(feature = "core")]
    Worker(authentik::worker::Cli),
    #[cfg(feature = "core")]
    Manage(Manage),
    Healthcheck(authentik::healthcheck::Cli),
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
    let tracing_crude = authentik::tracing::install_crude();
    info!(version = env!("CARGO_PKG_VERSION"), "authentik is starting");

    let cli: Cli = argh::from_env();

    // TODO: healthcheck
    match &cli.command {
        #[cfg(feature = "core")]
        Command::AllInOne(_) => Mode::set(Mode::AllInOne)?,
        #[cfg(feature = "core")]
        Command::Server(_) => Mode::set(Mode::Server)?,
        #[cfg(feature = "core")]
        Command::Worker(_) => Mode::set(Mode::Worker)?,
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
        Command::Healthcheck(_) => {}
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
        trace!("initializing Python");
        pyo3::Python::initialize();
        trace!("Python initialized");
    }

    ConfigManager::init()?;

    let _sentry = authentik::config::get()
        .error_reporting
        .enabled
        .then(authentik::tracing::sentry::install);

    authentik::tracing::install()?;
    drop(tracing_crude);

    if let Command::Healthcheck(args) = &cli.command {
        return authentik::healthcheck::run(args.clone());
    }

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

            ConfigManager::run(&mut tasks)?;

            let metrics = authentik::metrics::run(&mut tasks)?;

            #[cfg(feature = "core")]
            if Mode::get() == Mode::AllInOne || Mode::get() == Mode::Worker {
                authentik::db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::AllInOne(_) => {
                    let workers =
                        authentik::worker::run(authentik::worker::Cli::default(), &mut tasks)?;
                    metrics.workers.store(Some(workers));
                    let server =
                        authentik::server::run(authentik::server::Cli::default(), &mut tasks)?;
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Server(args) => {
                    let server = authentik::server::run(args, &mut tasks)?;
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Worker(args) => {
                    let workers = authentik::worker::run(args, &mut tasks)?;
                    metrics.workers.store(Some(workers));
                }
                #[cfg(feature = "core")]
                Command::Manage(_) => unreachable!(),
                Command::Healthcheck(_) => unreachable!(),
            }

            let errors = tasks.run().await;

            Mode::cleanup();

            if errors.is_empty() {
                info!("authentik exiting");
                Ok(())
            } else {
                error!(?errors, "authentik encountered errors");
                Err(eyre!("Errors encountered: {:?}", errors))
            }
        })
}
