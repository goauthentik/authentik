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
    Boot(boot::Cli),
    #[cfg(feature = "core")]
    AllInOne(AllInOne),
    #[cfg(feature = "core")]
    Server(server::Cli),
    #[cfg(feature = "core")]
    Worker(worker::Cli),
    #[cfg(feature = "proxy")]
    Proxy(outpost::proxy::Cli),
    Healthcheck(healthcheck::Cli),
}

#[derive(Debug, FromArgs, PartialEq)]
/// Run both the authentik server and worker.
#[argh(subcommand, name = "allinone")]
#[expect(
    clippy::empty_structs_with_brackets,
    reason = "argh doesn't support unit structs"
)]
pub(crate) struct AllInOne {}

/// Parse the command line, allowing for the `/lifecycle/ak` symlink.
///
/// The container ships `/lifecycle/ak` as a symlink to this binary, because the
/// documented management commands are all invoked as `ak <command>`. When we
/// are called under that name, insert the `boot` subcommand.
#[expect(
    clippy::print_stdout,
    clippy::exit,
    reason = "argh reports --help and --version as an EarlyExit that must be printed"
)]
fn parse_args() -> Cli {
    let argv: Vec<String> = std::env::args().collect();
    let (program, rest) = argv
        .split_first()
        .map_or(("authentik", &[][..]), |(p, r)| (p.as_str(), r));

    #[cfg(feature = "core")]
    let inserted: Vec<&str> = if boot::invoked_as_ak(program) {
        std::iter::once("boot")
            .chain(rest.iter().map(String::as_str))
            .collect()
    } else {
        rest.iter().map(String::as_str).collect()
    };
    #[cfg(not(feature = "core"))]
    let inserted: Vec<&str> = rest.iter().map(String::as_str).collect();

    Cli::from_args(&[program], &inserted).unwrap_or_else(|early_exit| {
        print!("{}", early_exit.output);
        std::process::exit(i32::from(early_exit.status.is_err()));
    })
}

fn main() -> Result<()> {
    let tracing_crude = ak_tracing::install_crude();
    info!(version = authentik_full_version(), "authentik is starting");

    let cli = parse_args();

    match &cli.command {
        // The entrypoint execs away, so handle it before anything is set up.
        #[cfg(feature = "core")]
        Command::Boot(args) => return boot::run(args),
        #[cfg(feature = "core")]
        Command::AllInOne(_) => Mode::set(Mode::AllInOne)?,
        #[cfg(feature = "core")]
        Command::Server(_) => Mode::set(Mode::Server)?,
        #[cfg(feature = "core")]
        Command::Worker(_) => Mode::set(Mode::Worker)?,
        #[cfg(feature = "proxy")]
        Command::Proxy(_) => Mode::set(Mode::Proxy)?,
        Command::Healthcheck(args) => return healthcheck::run(args),
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
                Command::Boot(_) => unreachable!(),
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
