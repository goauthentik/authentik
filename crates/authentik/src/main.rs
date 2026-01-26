use std::str::FromStr;

use argh::FromArgs;
use authentik_config::{Config, get_config};
use eyre::{Report, Result, eyre};
use tokio::{
    signal::unix::{Signal, SignalKind, signal},
    sync::broadcast,
    task::JoinSet,
};
use tokio_util::sync::CancellationToken;

struct SignalStreams {
    hup: Signal,
    int: Signal,
    quit: Signal,
    usr1: Signal,
    usr2: Signal,
    term: Signal,
}

impl SignalStreams {
    fn new() -> Result<Self> {
        Ok(Self {
            hup: signal(SignalKind::hangup())?,
            int: signal(SignalKind::interrupt())?,
            quit: signal(SignalKind::quit())?,
            usr1: signal(SignalKind::user_defined1())?,
            usr2: signal(SignalKind::user_defined2())?,
            term: signal(SignalKind::terminate())?,
        })
    }
}

async fn watch_signals(
    streams: SignalStreams,
    stop: CancellationToken,
    tx: broadcast::Sender<SignalKind>,
) -> Result<()> {
    let SignalStreams {
        mut hup,
        mut int,
        mut quit,
        mut usr1,
        mut usr2,
        mut term,
    } = streams;
    loop {
        tokio::select! {
            _ = hup.recv() => tx.send(SignalKind::interrupt())?,
            _ = int.recv() => tx.send(SignalKind::interrupt())?,
            _ = quit.recv() => tx.send(SignalKind::interrupt())?,
            _ = usr1.recv() => tx.send(SignalKind::user_defined1())?,
            _ = usr2.recv() => tx.send(SignalKind::user_defined2())?,
            _ = term.recv() => tx.send(SignalKind::terminate())?,
            _ = stop.cancelled() => return Ok(()),
        };
    }
}

#[derive(Debug, FromArgs, PartialEq)]
/// The authentication glue you need
struct Cli {
    #[argh(subcommand)]
    command: Command,
}

#[derive(Debug, FromArgs, PartialEq)]
#[argh(subcommand)]
enum Command {
    Server(authentik_server::Cli),
    Worker(authentik_worker::Cli),
}

fn install_tracing() -> Result<()> {
    use tracing_error::ErrorLayer;
    use tracing_subscriber::{filter::EnvFilter, fmt, prelude::*};

    let default = format!("{},postgres=info", get_config().log_level);
    let filter_layer = EnvFilter::builder()
        .with_default_directive(get_config().log_level.parse().expect("Invalid log_level"))
        .parse(default)?;
    let filter_layer = if let Some(directive) = &get_config().log {
        filter_layer.add_directive(directive.parse()?)
    } else {
        filter_layer
    };

    if get_config().debug {
        tracing_subscriber::registry()
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

#[tokio::main]
async fn main() -> Result<()> {
    color_eyre::install()?;
    Config::setup()?;

    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .unwrap();

    let _sentry = if get_config().error_reporting.enabled {
        Some(sentry::init(sentry::ClientOptions {
            // TODO: refine a bit more
            dsn: get_config()
                .error_reporting
                .sentry_dsn
                .clone()
                .map(|dsn| sentry::types::Dsn::from_str(&dsn).unwrap()),
            environment: Some(get_config().error_reporting.environment.clone().into()),
            attach_stacktrace: true,
            send_default_pii: get_config().error_reporting.send_pii,
            sample_rate: get_config().error_reporting.sample_rate,
            traces_sample_rate: get_config().error_reporting.sample_rate,
            ..sentry::ClientOptions::default()
        }))
    } else {
        None
    };

    install_tracing()?;
    let cli: Cli = argh::from_env();

    if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
        let mut dir = std::env::temp_dir();
        dir.push("authentik_prometheus_tmp");
        // SAFETY: there is only one thread at this point, so this is safe.
        unsafe {
            std::env::set_var("PROMETHEUS_MULTIPROC_DIR", dir);
        }
    }

    let stop = CancellationToken::new();
    let (signals_tx, _signals_rx) = broadcast::channel(10);

    let mut tasks = JoinSet::new();
    tasks.spawn(watch_signals(
        SignalStreams::new()?,
        stop.clone(),
        signals_tx.clone(),
    ));

    match cli.command {
        Command::Server(args) => {
            authentik_server::run(args, &mut tasks, stop.clone(), signals_tx.clone()).await?;
        }
        Command::Worker(_args) => todo!(),
    };

    if let Some(result) = tasks.join_next().await {
        stop.cancel();

        let mut errors = Vec::new();

        match result {
            Ok(Ok(_)) => {}
            Ok(Err(err)) => errors.push(err),
            Err(err) => errors.push(Report::new(err)),
        }

        while let Some(result) = tasks.join_next().await {
            match result {
                Ok(Ok(_)) => {}
                Ok(Err(err)) => errors.push(err),
                Err(err) => errors.push(Report::new(err)),
            }
        }

        if !errors.is_empty() {
            return Err(eyre!("Errors encountered: {:?}", errors));
        }
    }

    Ok(())
}
