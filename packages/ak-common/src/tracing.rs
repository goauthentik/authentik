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
    use std::{str::FromStr as _, time::Duration};

    use ak_client::apis::root_api::root_config_retrieve;
    use eyre::{Error, Result};
    use tokio_retry2::{Retry, RetryError, strategy::FixedInterval};
    use tracing::{error, trace};

    use crate::{
        Mode, VERSION, api, authentik_user_agent,
        config::{self, schema::ErrorReportingConfig},
    };

    fn get_config() -> Result<ErrorReportingConfig> {
        // In non-core mode, we are running an outpost and need to grab the error reporting
        // configuration from the API.
        if Mode::is_core() {
            return Ok(config::get().error_reporting.clone());
        }

        let api_config = api::make_config()?;

        let config = {
            let retry_strategy = FixedInterval::new(Duration::from_secs(3));
            let retrieve_config = async || {
                root_config_retrieve(&api_config)
                    .await
                    .map_err(Error::new)
                    .map_err(RetryError::transient)
            };
            let retry_notify = |err: &Error, _duration| {
                error!(
                    ?err,
                    "Failed to fetch configuration from API, retrying in 3 seconds"
                );
            };
            tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()?
                .block_on(Retry::spawn_notify(
                    retry_strategy,
                    retrieve_config,
                    retry_notify,
                ))?
        };

        let config = config.error_reporting;

        Ok(ErrorReportingConfig {
            enabled: config.enabled,
            sentry_dsn: Some(config.sentry_dsn),
            environment: config.environment,
            send_pii: config.send_pii,
            #[expect(
                clippy::cast_possible_truncation,
                reason = "This is fine, we'll never get big values here."
            )]
            #[expect(
                clippy::as_conversions,
                reason = "This is fine, we'll never get big values here."
            )]
            sample_rate: config.traces_sample_rate as f32,
        })
    }

    /// Install the sentry client. This must happen before [`super::install`] is called.
    pub fn install() -> Result<Option<sentry::ClientInitGuard>> {
        let config = get_config()?;
        if !config.enabled {
            return Ok(None);
        }
        trace!("setting up sentry");
        let debug = config::get().debug;
        Ok(Some(sentry::init(sentry::ClientOptions {
            dsn: config.sentry_dsn.clone().map(|dsn| {
                sentry::types::Dsn::from_str(&dsn).expect("Failed to create sentry DSN")
            }),
            release: Some(format!("authentik@{VERSION}").into()),
            environment: Some(config.environment.clone().into()),
            attach_stacktrace: true,
            send_default_pii: config.send_pii,
            sample_rate: config.sample_rate,
            traces_sample_rate: if debug { 1.0 } else { config.sample_rate },
            user_agent: authentik_user_agent().into(),
            ..sentry::ClientOptions::default()
        })))
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
