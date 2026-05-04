use std::{env::temp_dir, os::unix, path::PathBuf, sync::Arc};

use ak_axum::{router::wrap_router, server};
use ak_common::{
    arbiter::{Arbiter, Tasks},
    config,
};
use arc_swap::ArcSwapOption;
use axum::{Router, routing::any};
use eyre::Result;
use metrics_exporter_prometheus::{PrometheusBuilder, PrometheusHandle};
use tokio::{
    task::spawn_blocking,
    time::{Duration, interval},
};
use tracing::info;

#[cfg(feature = "core")]
use crate::worker::Workers;

mod handlers;

fn socket_path() -> PathBuf {
    temp_dir().join("authentik-metrics.sock")
}

pub(crate) struct Metrics {
    prometheus: PrometheusHandle,
    #[cfg(feature = "core")]
    pub(crate) workers: ArcSwapOption<Workers>,
}

impl Metrics {
    fn new() -> Result<Self> {
        info!("installing Prometheus recorder");
        let prometheus = PrometheusBuilder::new()
            .with_recommended_naming(true)
            .install_recorder()?;
        Ok(Self {
            prometheus,
            #[cfg(feature = "core")]
            workers: ArcSwapOption::empty(),
        })
    }
}

async fn run_upkeep(arbiter: Arbiter, state: Arc<Metrics>) -> Result<()> {
    info!("starting metrics upkeep runner");
    let mut upkeep_interval = interval(Duration::from_secs(5));
    loop {
        tokio::select! {
            _ = upkeep_interval.tick() => {
                let state_clone = Arc::clone(&state);
                spawn_blocking(move || state_clone.prometheus.run_upkeep()).await?;
            },
            () = arbiter.shutdown() => return Ok(())
        }
    }
}

fn build_router(state: Arc<Metrics>) -> Router {
    wrap_router(
        Router::new()
            .fallback(any(handlers::metrics_handler))
            .with_state(state),
        true,
    )
}

pub(crate) fn start(tasks: &mut Tasks) -> Result<Arc<Metrics>> {
    let arbiter = tasks.arbiter();
    let metrics = Arc::new(Metrics::new()?);
    let router = build_router(Arc::clone(&metrics));

    tasks
        .build_task()
        .name(&format!("{}::run_upkeep", module_path!()))
        .spawn(run_upkeep(arbiter, Arc::clone(&metrics)))?;

    for addr in config::get().listen.metrics.iter().copied() {
        server::start_plain(
            tasks,
            "metrics",
            router.clone(),
            addr,
            config::get().debug, /* Allow failure in case the server is running on the same
                                  * machine, like in dev */
        )?;
    }

    server::start_unix(
        tasks,
        "metrics",
        router,
        unix::net::SocketAddr::from_pathname(socket_path())?,
        config::get().debug, /* Allow failure in case the server is running on the same machine,
                              * like in dev */
    )?;

    Ok(metrics)
}
