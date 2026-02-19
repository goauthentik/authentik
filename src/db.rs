use std::{str::FromStr, sync::OnceLock, time::Duration};

use eyre::Result;
use sqlx::{
    PgPool,
    postgres::{PgConnectOptions, PgPoolOptions, PgSslMode},
};
use tokio::sync::broadcast;
use tracing::log::LevelFilter;

use crate::{
    arbiter::{Arbiter, Tasks},
    config::get_config,
};

static DB: OnceLock<PgPool> = OnceLock::new();

async fn get_connect_opts() -> Result<PgConnectOptions> {
    let config = get_config().await;
    let mut opts = PgConnectOptions::new()
        // TODO: get this from the mode
        .application_name("authentik")
        .host(&config.postgresql.host)
        .port(config.postgresql.port)
        .username(&config.postgresql.user)
        .password(&config.postgresql.password)
        .database(&config.postgresql.name)
        .ssl_mode(PgSslMode::from_str(&config.postgresql.sslmode)?)
        .options([
            // TODO: don't set this here, set it as a hook when creating the connection that runs
            // SET search_path = ..
            ("search_path", &config.postgresql.default_schema),
        ]);
    if let Some(sslrootcert) = &config.postgresql.sslrootcert {
        opts = opts.ssl_root_cert_from_pem(sslrootcert.as_bytes().to_vec());
    }
    if let Some(sslcert) = &config.postgresql.sslcert {
        opts = opts.ssl_client_cert_from_pem(sslcert.as_bytes());
    }
    if let Some(sslkey) = &config.postgresql.sslkey {
        opts = opts.ssl_client_key_from_pem(sslkey.as_bytes());
    }
    Ok(opts)
}

async fn update_connect_opts_on_config_change(
    arbiter: Arbiter,
    mut config_changed_rx: broadcast::Receiver<()>,
) -> Result<()> {
    loop {
        tokio::select! {
            res = config_changed_rx.recv() => {
                if res.is_err() {
                    break;
                }
                let db = get_db();
                db.set_connect_options(get_connect_opts().await?);
            },
            _ = arbiter.shutdown() => break,
        }
    }

    Ok(())
}

pub(crate) async fn init(
    tasks: &mut Tasks,
    config_changed_rx: broadcast::Receiver<()>,
) -> Result<()> {
    let options = get_connect_opts().await?;
    let config = get_config().await;

    let pool_options = PgPoolOptions::new()
        .min_connections(1)
        .max_connections(4)
        .acquire_time_level(LevelFilter::Trace)
        .max_lifetime(config.postgresql.conn_max_age.map(Duration::from_secs))
        .test_before_acquire(config.postgresql.conn_health_checks);

    let pool = pool_options.connect_with(options).await?;
    DB.get_or_init(|| pool);

    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!(
            "{}::update_connect_opts_on_config_change",
            module_path!(),
        ))
        .spawn(update_connect_opts_on_config_change(
            arbiter,
            config_changed_rx,
        ))?;

    Ok(())
}

pub(crate) fn get_db() -> &'static PgPool {
    DB.get()
        .expect("failed to get db, has it been initialized?")
}
