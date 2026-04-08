use std::{str::FromStr as _, sync::OnceLock, time::Duration};

use eyre::Result;
use sqlx::{
    ConnectOptions as _, Executor as _, PgConnection, PgPool,
    postgres::{PgConnectOptions, PgPoolOptions, PgSslMode},
};
use tracing::{info, log::LevelFilter, trace};

use crate::{
    arbiter::{Arbiter, Event, Tasks},
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
    let mut events_rx = arbiter.events_subscribe();
    info!("starting database watcher for config changes");
    loop {
        tokio::select! {
            Ok(Event::ConfigChanged) = events_rx.recv() => {
                trace!("config change received, refreshing database connection options");
                let db = get();
                db.set_connect_options(get_connect_opts()?);
            },
            () = arbiter.shutdown() => {
                info!("stopping database watcher for config changes");
                return Ok(());
            },
        }
    }
}

pub async fn init(tasks: &mut Tasks) -> Result<()> {
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

pub fn get() -> &'static PgPool {
    DB.get()
        .expect("failed to get db, has it been initialized?")
}

pub async fn create_conn() -> Result<PgConnection> {
    let options = get_connect_opts()?;
    let conn = options.connect().await?;
    Ok(conn)
}

#[cfg(test)]
mod tests {
    use serde_json::json;
    use sqlx::postgres::PgSslMode;
    use tokio::time::{Duration, sleep};

    use crate::{
        arbiter::{Event, Tasks},
        config,
    };

    #[tokio::test]
    async fn init() {
        std::env::set_current_dir(format!("{}/../../", env!("CARGO_MANIFEST_DIR")))
            .expect("failed to chdir");
        config::init().expect("failed to init config");
        let mut tasks = Tasks::new().expect("failed to create tasks");

        super::init(&mut tasks).await.expect("failed to init db");
    }

    #[tokio::test]
    async fn get() {
        std::env::set_current_dir(format!("{}/../../", env!("CARGO_MANIFEST_DIR")))
            .expect("failed to chdir");
        config::init().expect("failed to init config");
        let mut tasks = Tasks::new().expect("failed to create tasks");

        super::init(&mut tasks).await.expect("failed to init db");

        sqlx::query("SELECT 1")
            .execute(super::get())
            .await
            .expect("failed to execute query");
    }

    #[tokio::test]
    async fn conn_options() {
        std::env::set_current_dir(format!("{}/../../", env!("CARGO_MANIFEST_DIR")))
            .expect("failed to chdir");
        config::init().expect("failed to init config");
        let mut tasks = Tasks::new().expect("failed to create tasks");
        super::init(&mut tasks).await.expect("failed to init db");
        assert_eq!(config::get().postgresql.default_schema, "public");

        let row: (String,) = sqlx::query_as("SHOW search_path")
            .fetch_one(super::get())
            .await
            .expect("failed to run query");
        assert_eq!(row.0, "public");

        let row: (String,) = sqlx::query_as("SHOW application_name")
            .fetch_one(super::get())
            .await
            .expect("failed to run query");
        assert!(row.0.contains("authentik"));
    }

    #[tokio::test]
    async fn config_update() {
        std::env::set_current_dir(format!("{}/../../", env!("CARGO_MANIFEST_DIR")))
            .expect("failed to chdir");
        config::init().expect("failed to init config");
        let mut tasks = Tasks::new().expect("failed to create tasks");
        let arbiter = tasks.arbiter();

        super::init(&mut tasks).await.expect("failed to init db");
        // Wait for the background tasks to start.
        sleep(Duration::from_millis(100)).await;

        assert!(matches!(
            super::get().connect_options().get_ssl_mode(),
            PgSslMode::Disable
        ));

        config::set(json!({
            "postgresql": {
                "sslmode": "prefer",
            },
        }))
        .expect("failed to set config");
        arbiter
            .send_event(Event::ConfigChanged)
            .expect("failed to send config changed event");
        // Wait for the change to propagate.
        sleep(Duration::from_millis(100)).await;

        assert!(matches!(
            super::get().connect_options().get_ssl_mode(),
            PgSslMode::Prefer
        ));
    }

    #[tokio::test]
    async fn create_conn() {
        std::env::set_current_dir(format!("{}/../../", env!("CARGO_MANIFEST_DIR")))
            .expect("failed to chdir");
        config::init().expect("failed to init config");

        let mut conn = super::create_conn().await.expect("failed to create conn");

        sqlx::query("SELECT 1")
            .execute(&mut conn)
            .await
            .expect("failed to run query");
    }
}
