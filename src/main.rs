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

use authentik::{arbiter::Tasks, config::ConfigManager, mode::Mode, server, worker};

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
    let tracing_crude = authentik::tracing::install_crude();
    info!(version = env!("CARGO_PKG_VERSION"), "authentik is starting");

    let cli: Cli = argh::from_env();

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

            let metrics = authentik::metrics::run(&mut tasks)?;

            #[cfg(feature = "core")]
            if Mode::get() == Mode::AllInOne || Mode::get() == Mode::Worker {
                authentik::db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::AllInOne(_) => {
                    let workers = worker::run(worker::Cli::default(), &mut tasks)?;
                    metrics.workers.store(Some(Arc::clone(&workers)));
                    server::run(server::Cli::default(), &mut tasks)?;
                }
                #[cfg(feature = "core")]
                Command::Server(args) => {
                    server::run(args, &mut tasks)?;
                }
                #[cfg(feature = "core")]
                Command::Worker(args) => {
                    let workers = worker::run(args, &mut tasks)?;
                    metrics.workers.store(Some(workers));
                }
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
