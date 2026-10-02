use std::sync::atomic::{AtomicUsize, Ordering};

#[cfg(feature = "core")]
use ak_common::db;
use ak_common::{Mode, Tasks, authentik_full_version, config, tls, tracing as ak_tracing};
use argh::FromArgs;
use eyre::{Result, eyre};
use tracing::{error, info, trace};

#[cfg(feature = "core")]
mod boot;
#[cfg(feature = "core")]
pub(crate) mod brands;
mod healthcheck;
mod metrics;
#[cfg(feature = "proxy")]
pub(crate) mod outpost;
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
    AllInOne(AllInOne),
    #[cfg(feature = "core")]
    Server(server::Cli),
    #[cfg(feature = "core")]
    Worker(worker::Cli),
    #[cfg(feature = "proxy")]
    Proxy(outpost::proxy::Cli),
    Healthcheck(healthcheck::Cli),
    #[cfg(feature = "core")]
    Manage(boot::Manage),
    #[cfg(feature = "core")]
    TestAll(boot::TestAll),
    #[cfg(feature = "core")]
    DumpConfig(boot::DumpConfig),
    #[cfg(feature = "core")]
    Bash(boot::Bash),
    #[cfg(feature = "core")]
    Sh(boot::Sh),
    #[cfg(feature = "core")]
    Debug(boot::Debug),
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run both the authentik server and worker.
#[argh(subcommand, name = "allinone")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct AllInOne {}

fn main() -> Result<()> {
    let tracing_crude = ak_tracing::install_crude();

    let cli: Cli = argh::from_env();

    match &cli.command {
        #[cfg(feature = "core")]
        Command::AllInOne(_) => {
            boot::boot()?;
            Mode::set(Mode::AllInOne)?;
        }
        #[cfg(feature = "core")]
        Command::Server(_) => {
            boot::boot()?;
            Mode::set(Mode::Server)?;
        }
        #[cfg(feature = "core")]
        Command::Worker(_) => {
            boot::boot()?;
            Mode::set(Mode::Worker)?;
        }
        #[cfg(feature = "proxy")]
        Command::Proxy(_) => Mode::set(Mode::Proxy)?,
        Command::Healthcheck(args) => return healthcheck::run(args),
        // These don't run authentik itself, so they skip the setup below and its logging to stdout
        #[cfg(feature = "core")]
        Command::Manage(args) => return boot::manage(args),
        #[cfg(feature = "core")]
        Command::TestAll(_) => return boot::test_all(),
        #[cfg(feature = "core")]
        Command::DumpConfig(args) => return boot::dump_config(args),
        #[cfg(feature = "core")]
        Command::Bash(args) => return boot::bash(args),
        #[cfg(feature = "core")]
        Command::Sh(args) => return boot::sh(args),
        #[cfg(feature = "core")]
        Command::Debug(_) => boot::idle(),
    }

    info!(version = authentik_full_version(), "authentik is starting");

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
    let log_filter_handle = ak_tracing::install()?;
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
            if Mode::is_core() {
                db::init(&mut tasks).await?;
            }

            match cli.command {
                #[cfg(feature = "core")]
                Command::AllInOne(_) => {
                    let workers = worker::start(worker::Cli::default(), &mut tasks)?;
                    metrics.workers.store(Some(workers));
                    let server = server::start(server::Cli::default(), &mut tasks).await?;
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Server(args) => {
                    let server = server::start(args, &mut tasks).await?;
                    metrics.server.store(Some(server));
                }
                #[cfg(feature = "core")]
                Command::Worker(args) => {
                    let workers = worker::start(args, &mut tasks)?;
                    metrics.workers.store(Some(workers));
                }
                #[cfg(feature = "proxy")]
                Command::Proxy(args) => {
                    outpost::start::<outpost::proxy::ProxyOutpost>(
                        args,
                        &mut tasks,
                        Some(log_filter_handle),
                    )
                    .await?;
                }
                // We're checking for these before starting anything else
                #[cfg(feature = "core")]
                Command::Manage(_)
                | Command::TestAll(_)
                | Command::DumpConfig(_)
                | Command::Bash(_)
                | Command::Sh(_)
                | Command::Debug(_) => unreachable!(),
                Command::Healthcheck(_) => unreachable!(),
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
