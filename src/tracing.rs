use eyre::Result;
use tracing_subscriber::{filter::EnvFilter, fmt, prelude::*};

use crate::config;

fn format() -> fmt::format::Format {
    fmt::format()
        .with_thread_ids(true)
        .with_thread_names(true)
        .with_source_location(true)
}

pub(super) fn install() -> Result<()> {
    let config = config::get();

    let mut filter_layer = EnvFilter::builder()
        .with_default_directive(config.log_level.parse().expect("Invalid log_level"))
        .parse(&config.log_level)?;
    for (k, v) in &config.log.rust_log {
        filter_layer = filter_layer.add_directive(format!("{k}={v}").parse()?);
    }

    if config.debug {
        let console_layer = console_subscriber::ConsoleLayer::builder()
            .server_addr(config.listen.debug)
            .spawn();
        tracing_subscriber::registry()
            .with(console_layer)
            .with(filter_layer)
            .with(
                fmt::layer()
                    .event_format(format().compact())
                    .with_writer(std::io::stderr),
            )
            .with(sentry::integrations::tracing::layer())
            .init();
    } else {
        tracing_subscriber::registry()
            .with(filter_layer)
            .with(
                fmt::layer()
                    .event_format(format().json().flatten_event(true))
                    .with_writer(std::io::stderr),
            )
            .with(sentry::integrations::tracing::layer())
            .init();
    }

    Ok(())
}

pub(super) fn install_crude() -> tracing::dispatcher::DefaultGuard {
    let filter_layer = EnvFilter::builder()
        .parse("trace,console_subscriber=info,runtime=info,tokio=info,tungstenite=info")
        .expect("infallible");
    let subscriber = tracing_subscriber::registry().with(filter_layer).with(
        fmt::layer()
            .event_format(format().json().flatten_event(true))
            .with_writer(std::io::stderr),
    );
    tracing::dispatcher::set_default(&subscriber.into())
}
