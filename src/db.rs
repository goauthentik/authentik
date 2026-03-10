use std::{str::FromStr, sync::OnceLock, time::Duration};

use eyre::Result;
use sqlx::{
    Executor, PgPool,
    postgres::{PgConnectOptions, PgPoolOptions, PgSslMode},
};
use tracing::{info, log::LevelFilter, trace};

use crate::{
    arbiter::{Arbiter, Tasks},
    authentik_full_version, config,
    mode::Mode,
};

static DB: OnceLock<PgPool> = OnceLock::new();

fn get_connect_opts() -> Result<PgConnectOptions> {
    let config = config::get();
    let mut opts = PgConnectOptions::new()
        .application_name(&format!(
            "authentik-{}@{}",
            Mode::get(),
            authentik_full_version()
        ))
        .host(&config.postgresql.host)
        .port(config.postgresql.port)
        .username(&config.postgresql.user)
        .password(&config.postgresql.password)
        .database(&config.postgresql.name)
        .ssl_mode(PgSslMode::from_str(&config.postgresql.sslmode)?);
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

async fn update_connect_opts_on_config_change(arbiter: Arbiter) -> Result<()> {
    let mut config_changed_rx = arbiter.config_changed_subscribe();
    info!("starting database watcher for config changes");
    loop {
        tokio::select! {
            res = config_changed_rx.changed() => {
                if let Err(err) = res {
                    trace!("error receiving config changes: {err:?}");
                    break;
                }
                trace!("config change recevied, refreshing database connection options");
                let db = get();
                db.set_connect_options(get_connect_opts()?);
            },
            () = arbiter.shutdown() => break,
        }
    }

    info!("stopping database watcher for config changes");
    Ok(())
}

pub(crate) async fn init(tasks: &mut Tasks) -> Result<()> {
    info!("initializing database pool");
    let options = get_connect_opts()?;
    let config = config::get();

    let pool_options = PgPoolOptions::new()
        .min_connections(1)
        .max_connections(4)
        .acquire_time_level(LevelFilter::Trace)
        .max_lifetime(config.postgresql.conn_max_age.map(Duration::from_secs))
        .test_before_acquire(config.postgresql.conn_health_checks)
        .after_connect(|conn, _meta| {
            Box::pin(async move {
                let application_name =
                    format!("authentik-{}@{}", Mode::get(), authentik_full_version());
                let default_schema = &config::get().postgresql.default_schema;
                let query = format!(
                    "SET application_name = '{application_name}'; SET search_path = \
                     '{default_schema}';"
                );
                conn.execute(query.as_str()).await?;
                Ok(())
            })
        });

    let pool = pool_options.connect_with(options).await?;
    DB.get_or_init(|| pool);

    let arbiter = tasks.arbiter();
    tasks
        .build_task()
        .name(&format!(
            "{}::update_connect_opts_on_config_change",
            module_path!(),
        ))
        .spawn(update_connect_opts_on_config_change(arbiter))?;

    info!("database pool initialized");
    Ok(())
}

pub(crate) fn get() -> &'static PgPool {
    DB.get()
        .expect("failed to get db, has it been initialized?")
}
