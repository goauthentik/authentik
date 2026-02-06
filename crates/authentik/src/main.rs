use std::str::FromStr;

use argh::FromArgs;
use authentik_config::{ConfigManager, get_config};
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

#[tokio::main]
async fn main() -> Result<()> {
    let mut tasks = JoinSet::new();
    let stop = CancellationToken::new();

    let (config_changed_tx, config_changed_rx) = broadcast::channel(100);

    color_eyre::install()?;
    ConfigManager::init(&mut tasks, stop.clone(), config_changed_tx.clone()).await?;

    rustls::crypto::aws_lc_rs::default_provider()
        .install_default()
        .unwrap();

    let _sentry = if get_config().await.error_reporting.enabled {
        Some(sentry::init(sentry::ClientOptions {
            // TODO: refine a bit more
            dsn: get_config()
                .await
                .error_reporting
                .sentry_dsn
                .clone()
                .map(|dsn| sentry::types::Dsn::from_str(&dsn).unwrap()),
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

    if std::env::var("PROMETHEUS_MULTIPROC_DIR").is_err() {
        let mut dir = std::env::temp_dir();
        dir.push("authentik_prometheus_tmp");
        // SAFETY: there is only one thread at this point, so this is safe.
        unsafe {
            std::env::set_var("PROMETHEUS_MULTIPROC_DIR", dir);
        }
    }

    let (signals_tx, _signals_rx) = broadcast::channel(10);

    tasks.spawn(watch_signals(
        SignalStreams::new()?,
        stop.clone(),
        signals_tx.clone(),
    ));

    authentik_db::init(&mut tasks, stop.clone(), config_changed_rx).await?;

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
