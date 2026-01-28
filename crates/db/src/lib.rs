use std::sync::OnceLock;
use std::{str::FromStr, time::Duration};

use authentik_config::get_config;
use eyre::Result;
use sea_orm::DatabaseConnection;
use sqlx::{
    PgPool,
    postgres::{PgConnectOptions, PgPoolOptions, PgSslMode},
};
use tokio::{sync::broadcast, task::JoinSet};
use tokio_util::sync::CancellationToken;
use tracing::log::LevelFilter;

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
    stop: CancellationToken,
    mut config_changed_rx: broadcast::Receiver<()>,
) -> Result<()> {
    loop {
        tokio::select! {
            res = config_changed_rx.recv() => {
                if res.is_err() {
                    break;
                }
                let db = get_raw_db();
                db.set_connect_options(get_connect_opts().await?);
            },
            _ = stop.cancelled() => break,
        }
    }

    Ok(())
}

pub async fn init(
    tasks: &mut JoinSet<Result<()>>,
    stop: CancellationToken,
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

    tasks.spawn(update_connect_opts_on_config_change(
        stop,
        config_changed_rx,
    ));

    Ok(())
}

pub fn get_db() -> DatabaseConnection {
    DatabaseConnection::from(get_raw_db().clone())
}

pub fn get_raw_db() -> &'static PgPool {
    DB.get().unwrap()
}
