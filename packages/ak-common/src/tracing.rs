use eyre::Result;
use time::macros::format_description;
use tracing_error::ErrorLayer;
use tracing_subscriber::{
    filter::EnvFilter,
    fmt::{self, time::LocalTime},
    prelude::*,
};

use crate::config;

/// Install a tracing subscriber for watching tracing events.
///
/// If debug mode, will also install a console subscriber, which can be connected to with
/// `tokio-console`.
///
/// This method depends on the [`config`] and [`sentry`] being initialized. For logging before that
/// happens, see [`install_crude`].
pub fn install() -> Result<()> {
    let config = config::get();

    let time_format =
        format_description!("[year]-[month]-[day]T[hour]:[minute]:[second].[subsecond digits:6]");

    let mut filter_layer = EnvFilter::builder()
        .with_default_directive(config.log_level.parse()?)
        .parse(&config.log_level)?;
    for (k, v) in &config.log.rust_log {
        filter_layer = filter_layer.add_directive(format!("{k}={v}").parse()?);
    }

    if config.debug {
        let console_layer = console_subscriber::ConsoleLayer::builder()
            .server_addr(config.listen.debug_tokio)
            .spawn();
        tracing_subscriber::registry()
            .with(ErrorLayer::default())
            .with(console_layer)
            .with(
                fmt::layer()
                    .compact()
                    .event_format(
                        fmt::format()
                            .with_timer(LocalTime::new(time_format))
                            .with_thread_ids(true)
                            .with_thread_names(true)
                            .with_source_location(true)
                            .compact(),
                    )
                    .with_writer(std::io::stderr)
                    .with_filter(filter_layer),
            )
            .with(::sentry::integrations::tracing::layer())
            .init();
    } else {
        tracing_subscriber::registry()
            .with(ErrorLayer::default())
            .with(json::layer().with_filter(filter_layer))
            .with(::sentry::integrations::tracing::layer())
            .init();
    }

    Ok(())
}

/// Install a very basic tracing subscriber until a fully-featured one can be installed.
#[must_use]
pub fn install_crude() -> tracing::dispatcher::DefaultGuard {
    let filter_layer = EnvFilter::builder()
        .parse("trace,console_subscriber=info,runtime=info,tokio=info,tungstenite=info")
        .expect("infallible");
    let subscriber = tracing_subscriber::registry()
        .with(ErrorLayer::default())
        .with(filter_layer)
        .with(json::layer());
    tracing::dispatcher::set_default(&subscriber.into())
}

/// Utilities for JSON logging
mod json {
    use std::collections::HashMap;

    use time::macros::format_description;
    use tracing::Subscriber;
    use tracing_subscriber::{fmt::time::LocalTime, layer::Layer, registry::LookupSpan};

    /// Create a custom layer for JSON formatting, with:
    ///
    /// - local time
    /// - "message" key renamed to "event"
    /// - span data
    /// - current process id
    /// - thread information
    pub(super) fn layer<S>() -> impl Layer<S>
    where
        S: Subscriber + for<'lookup> LookupSpan<'lookup>,
    {
        let time_format = format_description!(
            "[year]-[month]-[day]T[hour]:[minute]:[second].[subsecond digits:6]"
        );

        let mut json_layer = json_subscriber::fmt::layer()
            .with_timer(LocalTime::new(time_format))
            .with_file(true)
            .with_line_number(true)
            .flatten_event(true)
            .flatten_current_span_on_top_level(true);

        let inner_layer = json_layer.inner_layer_mut();
        inner_layer.with_thread_ids("thread_id");
        inner_layer.with_thread_names("thread_name");
        inner_layer.add_dynamic_field("pid", |_, _| {
            Some(serde_json::Value::Number(serde_json::Number::from(
                std::process::id(),
            )))
        });
        inner_layer.with_flattened_event_with_renames(
            move |name, map| match map.get(name) {
                Some(name) => name.as_str(),
                None => name,
            },
            HashMap::from([("message".to_owned(), "event".to_owned())]),
        );

        json_layer
    }
}

/// Utilities for Sentry
pub mod sentry {
    use std::str::FromStr as _;

    use tracing::trace;

    use crate::{VERSION, authentik_user_agent, config};

    /// Install the sentry client. This must happen before [`super::install`] is called.
    pub fn install() -> sentry::ClientInitGuard {
        trace!("setting up sentry");
        let config = config::get();
        sentry::init(sentry::ClientOptions {
            dsn: config.error_reporting.sentry_dsn.clone().map(|dsn| {
                sentry::types::Dsn::from_str(&dsn).expect("Failed to create sentry DSN")
            }),
            release: Some(format!("authentik@{VERSION}").into()),
            environment: Some(config.error_reporting.environment.clone().into()),
            attach_stacktrace: true,
            send_default_pii: config.error_reporting.send_pii,
            sample_rate: config.error_reporting.sample_rate,
            traces_sample_rate: if config.debug {
                1.0
            } else {
                config.error_reporting.sample_rate
            },
            user_agent: authentik_user_agent().into(),
            ..sentry::ClientOptions::default()
        })
    }
}

#[cfg(test)]
mod tests {
    use tracing::{error, trace};

    #[test]
    fn crude() {
        let _ = super::install_crude();
        trace!("test");
        error!("test");
    }

    #[test]
    fn default() {
        crate::config::init().expect("failed to init config");
        super::install().expect("failed to install tracing");
        trace!("test");
        error!("test");
    }

    #[test]
    fn both() {
        let tracing_crude = super::install_crude();
        trace!("test");
        error!("test");
        crate::config::init().expect("failed to init config");
        super::install().expect("failed to install tracing");
        trace!("test");
        error!("test");
        drop(tracing_crude);
        trace!("test");
        error!("test");
    }

    #[test]
    fn sentry_install() {
        crate::config::init().expect("failed to init config");
        let _ = super::sentry::install();
    }

    #[test]
    fn all() {
        let tracing_crude = super::install_crude();
        trace!("test");
        error!("test");
        crate::config::init().expect("failed to init config");
        let _sentry = super::sentry::install();
        trace!("test");
        error!("test");
        super::install().expect("failed to install tracing");
        trace!("test");
        error!("test");
        drop(tracing_crude);
        trace!("test");
        error!("test");
    }
}
