use argh::FromArgs;
use authentik_config::{Config, get_config};
use eyre::Result;
use std::str::FromStr;

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
    use tracing_subscriber::prelude::*;
    use tracing_subscriber::{filter::EnvFilter, fmt};

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

fn main() -> Result<()> {
    color_eyre::install()?;
    Config::setup()?;

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

    match cli.command {
        Command::Server(args) => authentik_server::run(args),
        Command::Worker(args) => authentik_worker::run(args),
    }
}
